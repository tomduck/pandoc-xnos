# Copyright 2015-2018 Thomas J. Duck.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""core.py: library code for the pandoc-fignos/eqnos/tablenos filters.

Overview
--------

Below is a short summary of what is available.  More details are
given in the function docstrings.

#### Globals ####

  * `STRTYPES` - a list of string types for this python version
  * `STDIN`/`STDOUT`/`STDERR` - streams for use with pandoc

#### Utility functions ####

  * `init()` - Determines and returns the pandoc version
  * `get_meta()` - Retrieves variables from a document's metadata

#### Element list functions ####

  * `quotify()` - Changes Quoted elements to quoted strings
  * `dollarfy()` - Changes Math elements to dollared strings
  * `extract_attrs()` - Extracts attribute strings

#### Actions and their factory functions ####

  * `join_strings()` - Joins adjacent strings in a pandoc document
  * `repair_refs()` - Repairs broken Cite elements in a document
  * `process_refs_factory()` - Makes functions that process
                               references
  * `replace_refs_factory()` - Makes functions that replace refs with
                               format-specific content
  * `attach_attrs_factory()` - Makes functions that attach attributes
                               to elements
  * `detach_attrs_factory()` - Makes functions that detach attributes
                               from elements
  * `insert_secnos_factory()` - Makes functions that insert section
                                numbers into attributes
  * `insert_rawblocks_factory()` - Makes function to insert
                                   non-duplicate Raw Block elements.
"""

import os
import sys
import io
import subprocess
import re
import textwrap
import functools
import copy

import psutil

from pandocfilters import Str, Space, Math, RawInline, RawBlock, Link
from pandocfilters import walk, stringify
from pandocfilters import elt as _elt

from .pandocattributes import PandocAttributes


#=============================================================================
# Globals

# Python has different string types depending on the python version.  We must
# be able to identify them both.
# pylint: disable=undefined-variable
STRTYPES = [str] if sys.version_info > (3,) else [str, unicode]

# Pandoc uses UTF-8 for both input and output; so must its filters.  This is
# handled differently depending on the python version.
if sys.version_info > (3,):
    # Py3 strings are unicode: https://docs.python.org/3.5/howto/unicode.html.
    # Character encoding/decoding is performed automatically at stream
    # interfaces: https://stackoverflow.com/questions/16549332/.
    # Set it to UTF-8 for all streams.
    STDIN = io.TextIOWrapper(sys.stdin.buffer, 'utf-8', 'strict')
    STDOUT = io.TextIOWrapper(sys.stdout.buffer, 'utf-8', 'strict')
    STDERR = io.TextIOWrapper(sys.stderr.buffer, 'utf-8', 'strict')
else:
    # Py2 strings are ASCII bytes.  Encoding/decoding is handled separately.
    # See: https://docs.python.org/2/howto/unicode.html.
    STDIN = sys.stdin
    STDOUT = sys.stdout
    STDERR = sys.stdout

# Privately flags that cleveref TeX needs to be written into the doc
# (for TeX/pdf output only).
_cleveref_tex_flag = False  # pylint: disable=invalid-name

# Used to track section numbers
# pylint: disable=invalid-name
MAXLEVEL = 1  # The maximum level header to track
sec = [0]     # Expand dynamically if needed


#=============================================================================
# Decorators

# _repeat() ------------------------------------------------------------------

# The _repeat decorator repeats a call until something other than None is
# returned.  Functions that must return None should be broken into parts.
# See, for example, join_strings().

def _repeat(func):
    """Repeats func(...) call until something other than None is returned."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Repeats the call until True is returned."""
        ret = None
        while ret is None:
            ret = func(*args, **kwargs)
        return ret
    return wrapper


#=============================================================================
# Utility functions

# init() ---------------------------------------------------------------------

_PANDOCVERSION = None  # A string giving the pandoc version

# pylint: disable=too-many-branches
def init(pandocversion=None, doc=None):
    """Sets or determines the pandoc version.  This must be called.

    The pandoc version is needed for multi-version support.
    See: https://github.com/jgm/pandoc/issues/2640

    Returns the pandoc version."""

    # This requires some care because we can't be sure that a call to 'pandoc'
    # will work.  It could be 'pandoc-1.17.0.2' or some other name.  Try
    # checking the parent process first, and only make a call to 'pandoc' as
    # a last resort.

    global _PANDOCVERSION  # pylint: disable=global-statement

    pattern = re.compile(r'^[1-2]\.[0-9]+(?:\.[0-9]+)?(?:\.[0-9]+)?$')

    if 'PANDOC_VERSION' in os.environ:  # Available for pandoc >= 1.19.1
        pandocversion = str(os.environ['PANDOC_VERSION'])

    if not pandocversion is None:
        # Test the result and if it is OK then store it in _PANDOCVERSION
        if pattern.match(pandocversion):
            _PANDOCVERSION = pandocversion
            return _PANDOCVERSION
        else:
            msg = 'Cannot understand pandocversion=%s'%pandocversion
            raise RuntimeError(msg)

    if not doc is None:
        if 'pandoc-api-version' in doc:
            # This could be either 1.18 or 1.19; there is no way to
            # distinguish them (but there isn't a use case in pandoc-fignos
            # and friends where it matters)
            _PANDOCVERSION = '1.18'
            return _PANDOCVERSION

    # Get the command
    try:  # Get the path for the parent process
        if os.name == 'nt':
            # psutil appears to work differently for windows
            command = psutil.Process(os.getpid()).parent().parent().exe()
        else:
            command = psutil.Process(os.getpid()).parent().exe()
        if not os.path.basename(command).startswith('pandoc'):
            raise RuntimeError('pandoc not found')
    except:  # pylint: disable=bare-except
        # Call whatever pandoc is available and hope for the best
        command = 'pandoc'

    # Make the call
    try:
        # Get the version number and confirm it conforms to expectations
        output = subprocess.check_output([command, '-v'])
        line = output.decode('utf-8').split('\n')[0]
        pandocversion = line.split(' ')[-1].strip()
    except: # pylint: disable=bare-except
        pandocversion = ''

    # Test the result and if it is OK then store it in _PANDOCVERSION
    if pattern.match(pandocversion):
        _PANDOCVERSION = pandocversion

    if _PANDOCVERSION is None:
        msg = """Cannot determine pandoc version.  Please file an issue at
              https://github.com/tomduck/pandocfiltering/issues"""
        raise RuntimeError(textwrap.dedent(msg))

    return _PANDOCVERSION


# get_meta() -----------------------------------------------------------------

# Metadata json depends upon whether or not the variables were defined on the
# command line or in a document.  The get_meta() function makes no
# distinction.

def get_meta(meta, name):
    """Retrieves the metadata variable 'name' from the 'meta' dict."""
    assert name in meta
    data = meta[name]
    if data['t'] in ['MetaString', 'MetaBool']:
        return data['c']
    elif data['t'] == 'MetaInlines':
        if len(data['c']) == 1:
            return stringify(data['c'])
    elif data['t'] == 'MetaList':
        return [stringify(v['c']) for v in data['c']]
    else:
        raise RuntimeError("Could not understand metadata variable '%s'." %
                           name)


# elt() ----------------------------------------------------------------------

def elt(eltType, numargs):  # pylint: disable=invalid-name
    """Returns Element(*value) to create pandoc json elements.

    This should be used in place of pandocfilters.elt().  This version
    ensures that the content is stored in a list, not a tuple.
    """
    def Element(*value):  # pylint: disable=invalid-name
        """Creates an element."""
        el = _elt(eltType, numargs)(*value)
        if type(el['c']) == tuple:
            el['c'] = list(el['c'])  # The content should be a list, not tuple
        return el
    return Element

Cite = elt('Cite', 2)  # pylint: disable=invalid-name

def _getel(key, value):
    """Returns an element given a key and value."""
    if key in ['HorizontalRule', 'Null']:
        return elt(key, 0)()
    elif key in ['Plain', 'Para', 'BlockQuote', 'BulletList',
                 'DefinitionList', 'HorizontalRule', 'Null']:
        return elt(key, 1)(value)
    else:
        return elt(key, len(value))(*value) # pylint: disable=star-args


#=============================================================================
# Element list functions

# quotify() ------------------------------------------------------------------

def quotify(x):
    """Replaces Quoted elements in element list 'x' with quoted strings.

    Pandoc uses the Quoted element in its json when --smart is enabled.
    Output to TeX/pdf automatically triggers --smart.

    stringify() ignores Quoted elements.  Use quotify() first to replace
    Quoted elements in 'x' with quoted strings.  'x' should be a deep copy so
    that the underlying document is left untouched.

    Returns x."""

    def _quotify(key, value, fmt, meta):  # pylint: disable=unused-argument
        """Replaced Quoted elements with quoted strings."""
        if key == 'Quoted':
            ret = []
            quote = '"' if value[0]['t'] == 'DoubleQuote' else "'"
            if value[1][0]['t'] == 'Str':
                value[1][0]['c'] = quote + value[1][0]['c']
            else:
                ret.append(Str(quote))

            if value[1][-1]['t'] == 'Str':
                value[1][-1]['c'] = value[1][-1]['c'] + quote
                ret += value[1]
            else:
                ret += value[1] + [Str(quote)]
            return ret

    return walk(walk(x, _quotify, '', {}), join_strings, '', {})


# dollarfy() -----------------------------------------------------------------

def dollarfy(x):
    """Replaces Math elements in element list 'x' with a $-enclosed string.

    stringify() passes through TeX math.  Use dollarfy(x) first to replace
    Math elements with math strings set in dollars.  'x' should be a deep copy
    so that the underlying document is left untouched.

    Returns 'x'."""

    def _dollarfy(key, value, fmt, meta):  # pylint: disable=unused-argument
        """Replaces Math elements"""
        if key == 'Math':
            return Str('$' + value[1] + '$')

    return walk(x, _dollarfy, '', {})


# extract_attrs() ------------------------------------------------------------

def extract_attrs(x, n):
    """Extracts attributes from element list 'x' beginning at index 'n'.

    The elements encapsulating the attributes (typically a series of Str and
    Space elements) are removed from 'x'.  Items before index 'n' are left
    unchanged.

    Returns the attributes in pandoc format.  A ValueError is raised if
    attributes aren't found.  An IndexError is raised if the index 'n' is out
    of range."""

    # Check for the start of the attributes string
    if not (x[n]['t'] == 'Str' and x[n]['c'].startswith('{')):
        raise ValueError('Attributes not found.')

    # It starts with {, so this *may* be an attributes list.  Search for where
    # the attributes end.  Do not consider } in quoted elements.

    seq = []          # A sequence of saved values
    quotechar = None  # Used to keep track of quotes in strings
    flag = False      # Flags that an attributes list was found
    i = 0             # Initialization

    for i, v in enumerate(x[n:]):  # Scan through the list
        if v and v['t'] == 'Str':
            # Scan for } outside of a quote
            for j, c in enumerate(v['c']):
                if c == quotechar:  # This is an end quote
                    quotechar = None
                elif c in ['"', "'"]:  # This is an open quote
                    quotechar = c
                elif c == '}' and quotechar is None:  # The attributes end here
                    # Split the string at the } and save the pieces
                    head, tail = v['c'][:j+1], v['c'][j+1:]
                    x[n+i] = copy.deepcopy(v)
                    x[n+i]['c'] = tail
                    v['c'] = head
                    flag = True
                    break
        seq.append(v)
        if flag:
            break

    if flag:  # Attributes string was found, so process it

        # Delete empty and extracted elements
        if x[n+i]['t'] == 'Str' and not x[n+i]['c']:
            del x[n+i]
        del x[n:n+i]

        # Process the attrs
        attrstr = stringify(dollarfy(quotify(seq))).strip()
        attrs = PandocAttributes(attrstr, 'markdown').to_pandoc()

        # Remove extranneous quotes from kvs
        for i, (k, v) in enumerate(attrs[2]):  # pylint: disable=unused-variable
            if v[0] == v[-1] == '"' or v[0] == "'" == v[-1] == "'":
                attrs[2][i][1] = attrs[2][i][1][1:-1]

        # We're done
        return attrs

    # Attributes not found
    raise ValueError('Attributes not found.')


#=============================================================================
# Actions and their factory functions

# Actions act on pandoc json elements. The pandocfilters.walk() function
# applies the action to all json elements in a document.  A non-None return
# value by an action is used by walk() to replace an element.  It is often
# easier to modify or delete elements from element lists in place.


# join_strings() -------------------------------------------------------------

# Pandoc never produces adjacent Str elements.  They may, however, arise from
# processing by actions.  This function joins adjacent string elements found
# in Para and Plain blocks.

# The design pattern used by this function is repeated by other actions,
# below. Processing of an element list 'x' is relegated to a helper.  The
# helper processes the list iteratively.  Processing is restarted (through use
# of the _repeat() decorator) any time the element list is changed.  A value
# of None is returned by the outer function because all modifications are made
# in place.

@_repeat
def _join_strings(x):
    """Joins adjacent Str elements found in the element list 'x'."""
    for i in range(len(x)-1):  # Process successive pairs of elements
        if x[i]['t'] == 'Str' and x[i+1]['t'] == 'Str':
            x[i]['c'] += x[i+1]['c']
            del x[i+1]  # In-place deletion of element from list
            return  # Forces processing to repeat
    return True  # Terminates processing

def join_strings(key, value, fmt, meta):  # pylint: disable=unused-argument
    """Joins adjacent Str elements in the 'value' list."""
    if key in ['Para', 'Plain']:
        _join_strings(value)
    elif key == 'Image':
        _join_strings(value[-2])
    elif key == 'Table':
        _join_strings(value[-5])


# repair_reference() ---------------------------------------------------------

# Reference regex.  This splits a reference into three components: the
# prefix, label and suffix.  e.g.:
# >>> _REF.match('xxx{+@fig:1}xxx').groups()
# ('xxx{+', 'fig:1', '}xxx').
_REF = re.compile(r'^((?:.*{)?[\*\+!]?)@([^:]*:[\w/-]+)(.*)')
def _is_broken_ref(key1, value1, key2, value2):
    """True if this is a broken reference; False otherwise."""
    # A link followed by a string may represent a broken reference
    if key1 != 'Link' or key2 != 'Str':
        return False
    # Assemble the parts
    n = 0 if _PANDOCVERSION < '1.16' else 1

    if type(value1[n][0]['c']) == list:
        # Occurs when there is quoted text in an actual link.  This is not
        # a broken link.  See Issue #1.
        return False

    s = value1[n][0]['c'] + value2
    # Return True if this matches the reference regex
    return True if _REF.match(s) else False

@_repeat
def _repair_refs(x):
    """Performs the repair on the element list 'x'."""

    if _PANDOCVERSION is None:
        raise RuntimeError('Module uninitialized.  Please call init().')

    # Scan the element list x
    for i in range(len(x)-1):

        # Check for broken references
        if _is_broken_ref(x[i]['t'], x[i]['c'] if 'c' in x[i] else [],
                          x[i+1]['t'], x[i+1]['c'] if 'c' in x[i+1] else []):

            # Get the reference string
            n = 0 if _PANDOCVERSION < '1.16' else 1
            s = x[i]['c'][n][0]['c'] + x[i+1]['c']

            # Chop it into pieces.  Note that the prefix and suffix may be
            # parts of other broken references.
            prefix, label, suffix = _REF.match(s).groups()

            # Insert the suffix, label and prefix back into x.  Do it in this
            # order so that the indexing works.
            if len(suffix):
                x.insert(i+2, Str(suffix))
            x[i+1] = Cite(
                [{"citationId":label,
                  "citationPrefix":[],
                  "citationSuffix":[],
                  "citationNoteNum":0,
                  "citationMode":{"t":"AuthorInText", "c":[]},
                  "citationHash":0}],
                [Str('@' + label)])
            if len(prefix):
                if i > 0 and x[i-1]['t'] == 'Str':
                    x[i-1]['c'] = x[i-1]['c'] + prefix
                    del x[i]
                else:
                    x[i] = Str(prefix)
            else:
                del x[i]

            return  # Forces processing to repeat

    return True  # Terminates processing

def repair_refs(key, value, fmt, meta):  # pylint: disable=unused-argument
    """Using "-f markdown+autolink_bare_uris" with pandoc < 1.18 splits a
    reference like "{@fig:one}" into email Link and Str elements.  This
    function replaces the mess with the Cite and Str elements we normally
    get.  Call this before any reference processing."""

    if _PANDOCVERSION >= '1.18':
        return

    # The problem spans multiple elements, and so can only be identified in
    # element lists.  Element lists are encapsulated in different ways.  We
    # must process them all.

    if key in ('Para', 'Plain'):
        _repair_refs(value)
    elif key == 'Image':
        _repair_refs(value[-2])
    elif key == 'Table':
        _repair_refs(value[-5])


# process_refs_factory() -----------------------------------------------------

def _get_label(key, value):
    """Gets the label from a reference."""
    assert key == 'Cite'
    return value[-1][0]['c'][1:]

def _extract_modifier(x, i, attrs):
    """Extracts the */+/! modifier in front of the Cite at index 'i' of the
    element list 'x'.  The modifier is stored in 'attrs'.  Returns the updated
    index 'i'."""

    global _cleveref_tex_flag  # pylint: disable=global-statement

    assert x[i]['t'] == 'Cite'
    assert i > 0

    # Check the previous element for a modifier in the last character
    if x[i-1]['t'] == 'Str':
        modifier = x[i-1]['c'][-1]
        if not _cleveref_tex_flag and modifier in ['*', '+']:
            _cleveref_tex_flag = True
        if modifier in ['*', '+', '!']:
            attrs[2].append(['modifier', modifier])
            if len(x[i-1]['c']) > 1:  # Lop the modifier off of the string
                x[i-1]['c'] = x[i-1]['c'][:-1]
            else:  # The element contains only the modifier; delete it
                del x[i-1]
                i -= 1

    return i

def _remove_brackets(x, i):
    """Removes curly brackets surrounding the Cite element at index 'i' in
    the element list 'x'.  It is assumed that the modifier has been
    extracted.  Empty strings are deleted from 'x'."""

    assert x[i]['t'] == 'Cite'
    assert i > 0 and i < len(x) - 1

    # Check if the surrounding elements are strings
    if not x[i-1]['t'] == x[i+1]['t'] == 'Str':
        return

    # Trim off curly brackets
    if x[i-1]['c'].endswith('{') and x[i+1]['c'].startswith('}'):
        if len(x[i+1]['c']) > 1:
            x[i+1]['c'] = x[i+1]['c'][1:]
        else:
            del x[i+1]

        if len(x[i-1]['c']) > 1:
            x[i-1]['c'] = x[i-1]['c'][:-1]
        else:
            del x[i-1]

@_repeat
def _process_refs(x, labels):
    """Strips surrounding curly braces and adds modifiers to the
    attributes of Cite elements.  Only references with labels in the 'labels'
    list are processed.  Repeats processing (via decorator) until no more
    broken references are found."""

    # Scan the element list x for Cite elements with known labels
    for i, v in enumerate(x):
        if v['t'] == 'Cite' and len(v['c']) == 2 and \
          _get_label(v['t'], v['c']) in labels:

            # A new reference was found; create some empty attributes for it
            attrs = ['', [], []]

            # Extract the modifiers.  'attrs' is updated in place.  Element
            # deletion could change the index of the Cite being processed.
            if i > 0:
                i = _extract_modifier(x, i, attrs)

            # Attach the attributes
            v['c'].insert(0, attrs)

            # Remove surrounding brackets
            if i > 0 and i < len(x)-1:
                _remove_brackets(x, i)

            # The element list may be changed
            return  # Forces processing to repeat via _repeat decorator

    return True  # Terminates processing in _repeat decorator

def process_refs_factory(labels):
    """Returns process_refs(key, value, fmt, meta) action that processes
    text around a reference.  Only references with labels found in the
    'labels' list are processed.

    Consider the markdown "{+@fig:1}", which represents a reference to a
    figure. "@" denotes a reference, "fig:1" is the reference's label, and
    "+" is a modifier.  Valid modifiers are '+, '*' and '!'.

    This function strips curly braces and adds the modifiers to the attributes
    of Cite elements.  Cite attributes must be detached before the document is
    written to STDOUT because pandoc doesn't recognize them.  Alternatively,
    use an action from replace_refs_factory() to replace the references
    altogether.
    """

    # pylint: disable=unused-argument
    def process_refs(key, value, fmt, meta):
        """Instates Ref elements."""
        # References may occur in a variety of places; we must process them
        # all.

        if key in ['Para', 'Plain']:
            _process_refs(value, labels)
        elif key == 'Image':
            _process_refs(value[-2], labels)
        elif key == 'Table':
            _process_refs(value[-5], labels)
        elif key == 'Span':
            _process_refs(value[-1], labels)
        elif key == 'Emph':
            _process_refs(value, labels)
        elif key == 'Strong':
            _process_refs(value, labels)

    return process_refs


# replace_refs_factory() ------------------------------------------------------

# pylint: disable=too-many-arguments
def replace_refs_factory(references, use_cleveref_default, use_eqref,
                         plusname, starname, target):
    """Returns replace_refs(key, value, fmt, meta) action that replaces
    references with format-specific content.  The content is determined using
    the 'references' dict, which associates reference labels with numbers or
    string tags (e.g., { 'fig:1':1, 'fig:2':2, ...}).  If 'use_cleveref_default'
    is True, or if "modifier" in the reference's attributes is "+" or "*", then
    clever referencing is used; i.e., a name is placed in front of the number
    or string tag.  The 'plusname' and 'starname' lists give the singular
    and plural names for "+" and "*" clever references, respectively.  The
    'target' is the LaTeX type for clever referencing (e.g., "figure",
    "equation", "table", ...)."""

    global _cleveref_tex_flag  # pylint: disable=global-statement

    # Update global if clever referencing is required by default
    _cleveref_tex_flag = _cleveref_tex_flag or use_cleveref_default

    def _insert_cleveref_fakery(key, value, meta):
        r"""Inserts TeX to support clever referencing in LaTeX documents
        if the key isn't a RawBlock.  If the key is a RawBlock, then check
        the value to see if the TeX was already inserted.

        The \providecommand macro is used to fake the cleveref package's
        behaviour if it is not provided in the template via
        \usepackage{cleveref}.

        TeX is inserted into the value.  Replacement elements are returned.
        """

        global _cleveref_tex_flag  # pylint: disable=global-statement

        comment1 = '% pandoc-xnos: cleveref formatting'
        tex1 = [comment1,
                r'\crefformat{%s}{%s~#2#1#3}'%(target, plusname[0]),
                r'\Crefformat{%s}{%s~#2#1#3}'%(target, starname[0])]

        if key == 'RawBlock':  # Check for existing cleveref TeX
            if value[1].startswith(comment1):
                # Append the new portion
                value[1] = value[1] + '\n' + '\n'.join(tex1[1:])
                _cleveref_tex_flag = False  # Cleveref fakery already installed

        elif key != 'RawBlock':  # Write the cleveref TeX
            _cleveref_tex_flag = False  # Cancels further attempts
            ret = []

            # Check first to see if fakery is turned off
            if not 'xnos-cleveref-fake' in meta or \
              get_meta(meta, 'xnos-cleveref-fake'):
                # Cleveref fakery
                tex2 = [
                    r'% pandoc-xnos: cleveref fakery',
                    r'\newcommand{\plusnamesingular}{}',
                    r'\newcommand{\starnamesingular}{}',
                    r'\newcommand{\xrefname}[1]{'\
                      r'\protect\renewcommand{\plusnamesingular}{#1}}',
                    r'\newcommand{\Xrefname}[1]{'\
                      r'\protect\renewcommand{\starnamesingular}{#1}}',
                    r'\providecommand{\cref}{\plusnamesingular~\ref}',
                    r'\providecommand{\Cref}{\starnamesingular~\ref}',
                    r'\providecommand{\crefformat}[2]{}',
                    r'\providecommand{\Crefformat}[2]{}']
                ret.append(RawBlock('tex', '\n'.join(tex2)))
            ret.append(RawBlock('tex', '\n'.join(tex1)))
            return ret

    def _cite_replacement(key, value, fmt, meta):
        """Returns context-dependent content to replace a Cite element."""

        assert key == 'Cite'

        attrs, label = value[0], _get_label(key, value)
        attrs = PandocAttributes(attrs, 'pandoc')

        assert label in references

        # Get the replacement value
        text = str(references[label])

        # Choose between \Cref, \cref and \ref
        use_cleveref = attrs['modifier'] in ['*', '+'] \
          if 'modifier' in attrs.kvs else use_cleveref_default
        plus = attrs['modifier'] == '+' if 'modifier' in attrs.kvs \
          else use_cleveref_default
        name = plusname[0] if plus else starname[0]  # Name used by cref

        # The replacement depends on the output format
        if fmt == 'latex':
            if use_cleveref:
                # Renew commands needed for cleveref fakery
                if not 'xnos-cleveref-fake' in meta or \
                  get_meta(meta, 'xnos-cleveref-fake'):
                    faketex = (r'\xrefname' if plus else r'\Xrefname') + \
                      '{%s}' % name
                else:
                    faketex = ''
                macro = r'\cref' if plus else r'\Cref'
                ret = RawInline('tex', r'%s%s{%s}'%(faketex, macro, label))
            elif use_eqref:
                ret = RawInline('tex', r'\eqref{%s}'%label)
            else:
                ret = RawInline('tex', r'\ref{%s}'%label)
        else:
            if use_eqref:
                text = '(' + text + ')'

            linktext = [Math({"t":"InlineMath", "c":[]}, text[1:-1]) \
               if text.startswith('$') and text.endswith('$') \
               else Str(text)]

            link = elt('Link', 2)(linktext, ['#%s' % label, '']) \
              if _PANDOCVERSION < '1.16' else \
              Link(['', [], []], linktext, ['#%s' % label, ''])
            ret = ([Str(name), Space()] if use_cleveref else []) + [link]

        return ret

    def replace_refs(key, value, fmt, meta):  # pylint: disable=unused-argument
        """Replaces references with format-specific content."""

        if fmt == 'latex' and _cleveref_tex_flag:

            # Put the cleveref TeX fakery in front of the first block element
            # that isn't a RawBlock.

            if not key in ['Plain', 'Para', 'CodeBlock', 'RawBlock',
                           'BlockQuote', 'OrderedList', 'BulletList',
                           'DefinitionList', 'Header', 'HorizontalRule',
                           'Table', 'Div', 'Null']:
                return

            # Reconstruct the block element
            el = _getel(key, value)

            # Insert cleveref TeX in front of the block element
            tex = _insert_cleveref_fakery(key, value, meta)
            if tex:
                return  tex + [el]

        elif key == 'Cite' and len(value) == 3:  # Replace the reference

            return _cite_replacement(key, value, fmt, meta)

    return replace_refs


# attach_attrs_factory() -----------------------------------------------------

# pylint: disable=redefined-outer-name
def attach_attrs_factory(f, extract_attrs=extract_attrs, allow_space=False):
    """Returns attach_attrs(key, value, fmt, meta) action that reads and
    attaches attributes to unattributed elements generated by the
    pandocfilters function f (e.g. pandocfilters.Math, etc).

    The extract_attrs() function should read the attributes and raise a
    ValueError or IndexError if attributes are not found.
    """

    # Get the name
    name = f.__closure__[0].cell_contents

    def _attach_attrs(x):
        """Extracts and attaches the attributes."""
        for i, v in enumerate(x):
            if v and v['t'] == name:  # Find where the attributes start
                n = i+1
                if allow_space and n < len(x) and x[n]['t'] == 'Space':
                    n += 1
                try:  # Extract the attributes
                    attrs = extract_attrs(x, n)
                    x[i]['c'].insert(0, attrs)
                except (ValueError, IndexError):
                    pass

    def attach_attrs(key, value, fmt, meta):  # pylint: disable=unused-argument
        """Attaches attributes to an element."""
        if key in ['Para', 'Plain']:
            _attach_attrs(value)

            # Image: Add pandoc's figure marker if warranted
            if len(value) == 1 and value[0]['t'] == 'Image':
                value[0]['c'][-1][1] = 'fig:'

    return attach_attrs


# detach_attrs_factory() ------------------------------------------------------

def detach_attrs_factory(f):
    """Returns detach_attrs(key, value, fmt, meta) action that detaches
    attributes attached to elements of type f (e.g. pandocfilters.Math, etc).
    Attributes provided natively by pandoc will be left as is."""

    # Get the name and standard length
    if len(f.__closure__) != 2:
        raise RuntimeError(f.__closure__)

    name = f.__closure__[0].cell_contents
    n = f.__closure__[1].cell_contents

    def detach_attrs(key, value, fmt, meta):  # pylint: disable=unused-argument
        """Detaches the attributes."""
        if key == name:
            assert len(value) <= n+1
            if len(value) == n+1:
                # Make sure value[0] represents attributes then delete
                assert len(value[0]) == 3
                assert type(value[0][0]) in STRTYPES
                assert type(value[0][1]) is list
                assert type(value[0][2]) is list
                del value[0]

    return detach_attrs


# insert_secnos_factory() ----------------------------------------------------

# pylint: disable=redefined-outer-name
def insert_secnos_factory(f):
    """Returns insert_secnos(key, value, fmt, meta) action that inserts
    section numbers into the attributes of elements of type f.
    """

    # Get the name
    name = f.__closure__[0].cell_contents

    def insert_secnos(key, value, fmt, meta):  # pylint: disable=unused-argument
        """Inserts section numbers into elements attributes."""

        global sec  # pylint: disable=global-statement

        if 'xnos-number-sections' in meta and \
          meta['xnos-number-sections']['c'] and \
          fmt in ['html', 'html5']:
            if key == 'Header':
                if 'unnumbered' in value[1][1]:
                    return
                level = value[0]
                n = level - len(sec)
                if n > 0:
                    sec.extend([0]*n)
                sec[level-1] += 1
                sec = sec[:MAXLEVEL]
            if key == name:
                s = '.'.join([str(n) for n in sec])
                value[0][2].insert(0, ['secno', s])

    return insert_secnos


# delete_secnos_factory() ----------------------------------------------------

# pylint: disable=redefined-outer-name
def delete_secnos_factory(f):
    """Returns delete_secnos(key, value, fmt, meta) action that deletes
    section numbers from the attributes of elements of type f.
    """

    # Get the name
    name = f.__closure__[0].cell_contents

    def delete_secnos(key, value, fmt, meta):  # pylint: disable=unused-argument
        """Deletes section numbers from elements attributes."""
        if 'xnos-number-sections' in meta and \
          meta['xnos-number-sections']['c'] and \
          fmt in ['html', 'html5']:
            if key == name and len(value[0][2]) and \
              value[0][2][0][0] == 'secno':
                del value[0][2][0]

    return delete_secnos


# install_rawblock_factory() -------------------------------------------------

def insert_rawblocks_factory(rawblocks):
    r"""Returns insert_rawblocks(key, value, fmt, meta) action that inserts
    non-duplicate RawBlock elements.
    """

    # pylint: disable=unused-argument
    def insert_rawblocks(key, value, fmt, meta):
        """Inserts non-duplicate RawBlock elements."""

        if not rawblocks:
            return

        # Put the RawBlock elements in front of the first block element that
        # isn't also a RawBlock.

        if not key in ['Plain', 'Para', 'CodeBlock', 'RawBlock',
                       'BlockQuote', 'OrderedList', 'BulletList',
                       'DefinitionList', 'Header', 'HorizontalRule',
                       'Table', 'Div', 'Null']:
            return

        if key == 'RawBlock':  # Remove duplicates
            rawblock = RawBlock(*value)  # pylint: disable=star-args
            if rawblock in rawblocks:
                rawblocks.remove(rawblock)
                return

        if rawblocks:  # Insert blocks
            el = _getel(key, value)
            return [rawblocks.pop(0) for i in range(len(rawblocks))] + [el]

    return insert_rawblocks

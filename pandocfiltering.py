"""pandocfiltering: constants and functions for pandoc filters."""

# Copyright 2015, 2016 Thomas J. Duck.
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

import os
import sys
import io
import subprocess
import re
import textwrap
import functools
import itertools
import copy

import psutil

from pandocfilters import Str, Para, Plain, Space, Cite
from pandocfilters import elt, walk, stringify

from pandocattributes import PandocAttributes


#-----------------------------------------------------------------------------
# PANDOCVERSION

PANDOCVERSION = None

def init(pandocversion=None):
    """Sets the pandoc version.  If pandocversion == None then automatic
    detection is attempted.
    """

    # This requires some care because we can't be sure that a call to 'pandoc'
    # will work.  It could be 'pandoc-1.17.0.2' or some other name.  Try
    # checking the parent process first, and only make a call to 'pandoc' as
    # a last resort.
    #
    # It would be helpful if pandoc gave version information in its metadata.
    # See: https://github.com/jgm/pandoc/issues/2640

    global PANDOCVERSION  # pylint: disable=global-statement

    pattern = re.compile(r'^1\.[0-9]+(?:\.[0-9]+)?(?:\.[0-9]+)?$')

    if not pandocversion is None:
        if pattern.match(pandocversion):
            PANDOCVERSION = pandocversion
            return
        else:
            msg = 'Cannot understand pandocversion=%s'%pandocversion
            raise RuntimeError(msg)

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

    # Test the result
    if pattern.match(pandocversion):
        PANDOCVERSION = pandocversion

    if PANDOCVERSION is None:
        msg = """Cannot determine pandoc version.  Please file an issue at
              https://github.com/tomduck/pandocfiltering/issues"""
        raise RuntimeError(textwrap.dedent(msg))


#-----------------------------------------------------------------------------
# STRTYPES

# pylint: disable=undefined-variable
STRTYPES = [str] if sys.version_info > (3,) else [str, unicode]


#-----------------------------------------------------------------------------
# STDIN, STDOUT and STDERR

# Pandoc uses UTF-8 for both input and output; so must we.
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


# Pandoc elements ------------------------------------------------------------

# Note: These elements are not recognized by pandoc!  You must remove them
# before returning the json to pandoc.

# pylint: disable=invalid-name
Ref = elt('Ref', 2)  # attrs, reference string


# Decorators -----------------------------------------------------------------

def repeat(func):
    """Repeats func(value, ...) call until something other than None is
    returned.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Repeats the call until True is returned."""
        ret = None
        while ret is None:
            ret = func(*args, **kwargs)
        return ret
    return wrapper


# getmeta(doc, name) ---------------------------------------------------------

def get_meta(meta, name):
    """Retrieves the metadata variable name from the dict meta."""
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


# quotify() ------------------------------------------------------------------

def quotify(x):
    """Replaces Quoted elements with quoted strings.

    Pandoc uses the Quoted element in its json when --smart is enabled.
    Output to TeX/pdf automatically triggers --smart.

    stringify() ignores Quoted elements.  Use quotify() first to replace
    Quoted elements in x with quoted strings.  You should provide a deep
    copy of x so that the document is left untouched.

    Returns x.
    """
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

    def _joinstrings(key, value, fmt, meta):  # pylint: disable=unused-argument
        """Combines adjacent Str elements."""
        if key == 'Para' or key == 'Plain':
            flag = False
            for i in range(len(value)-1):
                if value[i]['t'] == 'Str' and value[i+1]['t'] == 'Str':
                    value[i]['c'] += value[i+1]['c']
                    value[i+1] = None
                    flag = True
            if flag:
                while None in value:
                    value.remove(None)
                return Para(value) if key == 'Para' else Plain(value)

    return walk(walk(x, _quotify, '', {}), _joinstrings, '', {})


# dollarfy() -----------------------------------------------------------------

def dollarfy(x):
    """Replaces Math elements with a $-enclosed string.

    stringify() passes through TeX math.  Use dollarfy(x) first to replace
    Math elements with math strings set in dollars.  You should provide a
    deep copy of x so that the document is left untouched.

    Returns x.
    """
    def _dollarfy(key, value, fmt, meta):  # pylint: disable=unused-argument
        """Replaces Math elements"""
        if key == 'Math':
            return Str('$' + value[1] + '$')

    return walk(x, _dollarfy, '', {})


# pandocify() ----------------------------------------------------------------

def pandocify(s):
    """Returns a representation of the string s using pandoc elements.
    Like stringify(), all formatting is ignored.
    """
    toks = [Str(tok) for tok in s.split()]
    spaces = [Space()]*len(toks)
    ret = list(itertools.chain(*zip(toks, spaces)))  # Leaves a space at the end
    if s[0] == ' ':  # Add a space at the beginning if needed
        ret = [Space()] + ret
    return ret if s[-1] == ' ' else ret[:-1]  # Trim space at end if needed


# extract_attrs() ------------------------------------------------------------

def extract_attrs(value, n):
    """Extracts attributes from a value list beginning at index n.

    The attributes string is removed from the value list.  Value items before
    index n are left unchanged.

    Returns the attributes in pandoc format.  A ValueError is raised if
    attributes aren't found.
    """

    # Check for the start of the attributes string
    if not (value[n]['t'] == 'Str' and value[n]['c'].startswith('{')):
        raise ValueError('Attributes not found.')

    # It starts with {, so this *may* be an attributes list.  Search for where
    # the attributes end.  Do not consider } in quoted elements.

    seq = []          # A sequence of saved values
    quotechar = None  # Used to keep track of quotes in strings
    flag = False      # Flags that an attributes list was found
    i = 0             # Initialization

    for i, v in enumerate(value[n:]):  # Scan through the value list
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
                    value[n+i] = copy.deepcopy(v)
                    value[n+i]['c'] = tail
                    v['c'] = head
                    flag = True
                    break
        seq.append(v)
        if flag:
            break

    if flag:  # Attributes string was found, so process it

        # Delete empty and extracted elements
        if value[n+i]['t'] == 'Str' and not value[n+i]['c']:
            del value[n+i]
        del value[n:n+i]

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


# repair_refs() --------------------------------------------------------------

# Reference regex
_REF = re.compile(r'^((?:.*{)?[\*\+!]?)(@[^:]*:[\w/-]+)(.*)?')

def _is_broken_ref(key1, value1, key2, value2):
    """True if this is a broken reference; False otherwise."""
    if PANDOCVERSION is None:
        raise RuntimeError('Module uninitialized.  Please call init().')
    # A link followed by a string may represent a broken reference
    if key1 != 'Link' or key2 != 'Str':
        return False
    # Assemble the parts
    n = 0 if PANDOCVERSION < '1.16' else 1
    s = value1[n][0]['c'] + value2
    # Check if this matches the reference regexes and return
    return True if _REF.match(s) else False

@repeat
def _repair_refs(value):
    """Performs the repair.  Returns updated value list."""
    if PANDOCVERSION is None:
        raise RuntimeError('Module uninitialized.  Please call init().')
    flag = False  # Flags that a change has been made

    # Scan the value list
    for i in range(len(value)-1):

        # Check for broken references
        if _is_broken_ref(value[i]['t'], value[i]['c'],
                          value[i+1]['t'], value[i+1]['c']):
            flag = True  # Found broken reference

            # Get the reference string
            n = 0 if PANDOCVERSION < '1.16' else 1
            s = value[i]['c'][n][0]['c'] + value[i+1]['c']

            # Chop it into pieces.  Note that the prefix and suffix may be
            # parts of other broken references.
            prefix, ref, suffix = _REF.match(s).groups()

            # Put the suffix, reference and prefix back into the value list

            # Suffix
            if len(suffix):
                value.insert(i+2, Str(suffix))

            # Reference
            value[i+1] = Cite(
                [{"citationId":ref[1:],
                  "citationPrefix":[],
                  "citationSuffix":[],
                  "citationNoteNum":0,
                  "citationMode":{"t":"AuthorInText", "c":[]},
                  "citationHash":0}],
                [Str(ref)])
            value[i+1]['c'] = list(value[i+1]['c'])  # Needed for unit tests

            # Prefix
            if len(prefix):
                if i > 0 and value[i-1]['t'] == 'Str':
                    value[i-1]['c'] = value[i-1]['c'] + prefix
                    del value[i]
                else:
                    value[i] = Str(prefix)
            else:
                del value[i]

            return  # Forces processing to be repeated

    if not flag:  # No more broken refs left to process
        return value

def repair_refs(key, value, fmt, meta):  # pylint: disable=unused-argument
    """Using -f markdown+autolink_bare_uris splits braced references like
    {@label:id} at the ':' into Link and Str elements.  This function replaces
    the mess with the Cite and Str elements we normally expect.  Call this
    before any reference processing.
    """

    if key in ('Para', 'Plain'):
        _repair_refs(value)


# use_refs_factory() ---------------------------------------------------------

def _is_cite_ref(key, value, references):
    """True if Cite element is a reference; False otherwise.
    references - a list containing known references.
    """
    return key == 'Cite' and value[1][0]['c'][1:] in references

def _parse_cite_ref(key, value):
    """Parses a reference stored in a Cite element.
    Returns the reference string.
    """
    assert key == 'Cite'
    assert not value[0][0]['citationPrefix']
    assert not value[0][0]['citationSuffix']
    return value[1][0]['c'][1:]

def _process_modifier(value, i, attrs):
    """Trims */+/! modifier in front of the Cite element at index i
    and stores it as an attribute.  Returns the updated index i.
    """
    assert value[i]['t'] == 'Cite'
    if i > 0 and value[i-1]['t'] == 'Str':
        if value[i-1]['c'][-1] in ['*', '+', '!']:
            attrs[2].append(['modifier', value[i-1]['c'][-1]])
            if len(value[i-1]['c']) > 1:
                value[i-1]['c'] = value[i-1]['c'][:-1]
                return i
            else:
                del value[i-1]
                return i-1
    return i

def _remove_brackets(value, i):
    """Removes curly brackets surrounding the Ref element at index i.  This
    assumes that the modifier has already been trimmed.  Empty strings are
    deleted from the value list.
    """
    assert value[i]['t'] == 'Ref'

    # Check if there are surrounding elements
    if i-1 < 0 or i+1 >= len(value):
        return

    # Check if the surrounding elements are strings
    if not value[i-1]['t'] == value[i+1]['t'] == 'Str':
        return

    # Trim off curly brackets and set empty values to None
    if value[i-1]['c'].endswith('{') and value[i+1]['c'].startswith('}'):
        if len(value[i+1]['c']) > 1:
            value[i+1]['c'] = value[i+1]['c'][1:]
        else:
            del value[i+1]

        if len(value[i-1]['c']) > 1:
            value[i-1]['c'] = value[i-1]['c'][:-1]
        else:
            del value[i-1]

@repeat
def _use_refs(value, references):
    """Replaces Cite references with Ref elements."""

    # Scan the values list in search of Cite references
    for i, v in enumerate(value):
        if v and _is_cite_ref(v['t'], v['c'], references):

            # A reference was found; extract its attributes
            attrs = ['', [], []]  # Initialized to empty
            if i+1 < len(value):
                try:  # Look for attributes in { ... }
                    attrs = extract_attrs(value, i+1)
                except ValueError:
                    pass

             # Process modifiers
            if i > 0:
                i = _process_modifier(value, i, attrs)

            # Insert the Ref element
            value[i] = Ref(attrs, _parse_cite_ref(v['t'], v['c']))
            value[i]['c'] = list(value[i]['c'])  # Needed for unit tests

            # Remove surrounding brackets
            _remove_brackets(value, i)

            # The value list may be changed
            return  # Forces processing to repeat given new value list

    return True  # Ends processing


def use_refs_factory(references):
    """Returns use_refs(key, value, fmt, meta) function that replaces
    known references with Ref elements.  Ref elements aren't understood by
    pandoc, but are easily identified for further processing by a filter.
    """

    if not references:
        references = []

    # pylint: disable=unused-argument
    def use_refs(key, value, fmt, meta):
        """Replaces known references with Ref elements."""

        if key in ['Para', 'Plain']:
            _use_refs(value, references)

    return use_refs


# use_attr_factory() ---------------------------------------------------------

# pylint: disable=redefined-outer-name
def use_attr_factory(name, extract_attrs=extract_attrs, allow_space=False):
    """Returns use_attr(key, value, fmt, meta) action that replaces elements
    of type name with attributed versions when attributes are found.

    The extract_attrs() function should read the attributes and raise a
    ValueError or IndexError if attributes are not found.
    """

    def _use_attr(value):
        """Extracts and attaches the attributes."""
        for i, v in enumerate(value):
            if v and v['t'] == name:
                n = i+1
                if allow_space and n < len(value) and \
                  value[n]['t'] == 'Space':
                    n += 1
                try:
                    attrs = extract_attrs(value, n)
                    value[i]['c'].insert(0, attrs)
                except (ValueError, IndexError):
                    pass

    def use_attr(key, value, fmt, meta):  # pylint: disable=unused-argument
        """Extracts attributes and attaches them to element."""
        if key in ['Para', 'Plain']:
            _use_attr(value)

            # Image: Add pandoc's figure marker if warranted
            if len(value) == 1 and value[0]['t'] == 'Image':
                value[0]['c'][2][1] = 'fig:'

    return use_attr


# filter_attr_factory() ------------------------------------------------------

def filter_attr_factory(name, n):
    """Returns filter_attr(key, value, fmt, meta) action that replaces named
    elements with unattributed versions of standard length n.
    """

    def filter_attr(key, value, fmt, meta):  # pylint: disable=unused-argument
        """Replaces attributed elements with their unattributed counterparts."""
        if key == name and len(value) == n+1:
            del value[0]

    return filter_attr

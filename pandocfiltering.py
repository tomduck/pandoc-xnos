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

if sys.version_info > (3,):
    from urllib.request import unquote  # pylint: disable=no-name-in-module
else:
    from urllib import unquote  # pylint: disable=no-name-in-module


#-----------------------------------------------------------------------------
# PANDOCVERSION

PANDOCVERSION = None

def init(pandocversion=None):
    """Sets the pandoc version.  If pandocversion == None then automatic
    detection is attempted.   This requires some care because we can't be
    sure that a call to 'pandoc' will work.  It could be 'pandoc-1.17.0.2' or
    some other name.  Try checking the parent process first, and only make a
    call to 'pandoc' as a last resort.

    It would be helpful if pandoc gave version information in its metadata.
    See: https://github.com/jgm/pandoc/issues/2640
    """

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

# Note: These elements are not recognized by pandoc!  You must be sure to
# remove them before sending the json back to pandoc.

# pylint: disable=invalid-name
AttrImage = elt('Image', 3)  # Same as Image for pandoc>=1.16
Ref = elt('Ref', 4)          # attrs, prefix, label, suffix

# Decorators -----------------------------------------------------------------

def filter_null(func):
    """Wraps func(value, ...).  Removes None values from the value list
    after modified by func().  The filtering is done *in place*.  Returns the
    results from func().
    """
    @functools.wraps(func)
    def wrapper(value, *args, **kwargs):
        """Performs the filtering."""
        ret = func(value, *args, **kwargs)
        while None in value:
            value.remove(None)
        return ret
    return wrapper

def _repeat_until_successful(func):
    """Repeats the call to func(value, ...) until a result is returned."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Repeats the call until True is returned."""
        ret = None
        while ret is None:
            ret = func(*args, **kwargs)
        return ret
    return wrapper


#-----------------------------------------------------------------------------
# quotify()

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


#-----------------------------------------------------------------------------
# dollarfy()

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


#-----------------------------------------------------------------------------
# pandocify()

def pandocify(s):
    """Returns a representation of the string s using pandoc elements.
    Like stringify(), all formatting is ignored.
    """
    toks = [Str(tok) for tok in s.split()]
    spaces = [Space()]*len(toks)
    ret = list(itertools.chain(*zip(toks, spaces)))
    if s[0] == ' ':
        ret = [Space()] + ret
    return ret if s[-1] == ' ' else ret[:-1]


#-----------------------------------------------------------------------------
# extract_attrs()

def extract_attrs(value, n):
    """Extracts attributes from a value list.  n is the index where the
    attributes start.  Extracted elements are set to None in the value list.
    Returns the attributes in pandoc format.
    """
    assert value[n:] and value[n]['t'] == 'Str' and \
      value[n]['c'].startswith('{')

    # It starts with {, so this may be an attributes list.  Do not
    # consider } in quoted elements.
    seq = []          # The sequence of saved values
    quotechar = None  # Keeps track of quotes in strings
    flag = False      # Flags that an attributes list is found
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
                    head, tail = v['c'][:j+1], v['c'][j+1:]
                    value[n+i] = copy.deepcopy(v)
                    value[n+i]['c'] = tail
                    v['c'] = head
                    flag = True
                    break
        seq.append(v)
        if flag:
            break

    if flag:

        # Nullify extracted and empty elements
        value[n:n+i] = [None]*i
        if not value[n+i]['c']:
            value[n+i] = None

        # Process the attrs and return them
        attrstr = stringify(dollarfy(quotify(seq))).strip()
        attrs = PandocAttributes(attrstr, 'markdown').to_pandoc()
        for i, (k, v) in enumerate(attrs[2]):  # pylint: disable=unused-variable
            if v[0] == v[-1] == '"' or v[0] == "'" == v[-1] == "'":
                attrs[2][i][1] = attrs[2][i][1][1:-1]
        return attrs

    else:
        raise RuntimeError('Attributes not found.')


#-----------------------------------------------------------------------------
# repair_refs() action

_PRE = re.compile(r'{[\+-]?@')

def _is_broken_ref(key1, value1, key2, value2):
    """True if this is a broken reference; False otherwise."""
    if PANDOCVERSION is None:
        raise RuntimeError('Module uninitialized.  Please call init().')
    if PANDOCVERSION < '1.16':
        return key1 == 'Link' and value1[0][0]['t'] == 'Str' and \
          _PRE.search(value1[0][0]['c']) and key2 == 'Str' and '}' in value2
    else:
        return key1 == 'Link' and value1[1][0]['t'] == 'Str' and \
          _PRE.search(value1[1][0]['c']) and key2 == 'Str' and '}' in value2

@_repeat_until_successful
@filter_null
def _repair_refs(value):
    """Performs the repair."""
    if PANDOCVERSION is None:
        raise RuntimeError('Module uninitialized.  Please call init().')
    flag = False  # Flags that a change has been made
    for i in range(len(value)-1):
        if value[i] == None:
            continue
        if _is_broken_ref(value[i]['t'], value[i]['c'],
                          value[i+1]['t'], value[i+1]['c']):
            flag = True  # Found broken reference
            if PANDOCVERSION < '1.16':
                s1 = value[i]['c'][0][0]['c']  # Get the first half of the ref
            else:
                s1 = value[i]['c'][1][0]['c']  # Get the first half of the ref
            s2 = value[i+1]['c']               # Get the second half of the ref
            # Form the reference
            x = _PRE.search(s1).group()
            ref = s1[s1.index(x)+len(x)-1:] + s2[:s2.index('}')]
            prefix = s1[:s1.index(x)+len(x)-1]  # Get the prefix
            suffix = s2[s2.index('}'):]  # Get the suffix
            # We need to be careful with the prefix string because it might be
            # part of another broken reference.  Simply put it back into the
            # value list and repeat the repair_broken_refs() call.
            if i > 0 and value[i-1]['t'] == 'Str':
                value[i-1]['c'] = value[i-1]['c'] + prefix
                value[i] = None
            else:
                value[i] = Str(prefix)
            # Put fixed reference in as a citation that can be processed
            value[i+1] = Cite(
                [{"citationId":ref[1:],
                  "citationPrefix":[],
                  "citationSuffix":[],
                  "citationNoteNum":0,
                  "citationMode":{"t":"AuthorInText", "c":[]},
                  "citationHash":0}],
                [Str(ref)])
            value[i+1]['c'] = list(value[i+1]['c'])  # Needed for unit tests
            # Insert the suffix
            value.insert(i+2, Str(suffix))
    if not flag:  # No more broken refs left to process
        return value

def repair_refs(key, value, fmt, meta):  # pylint: disable=unused-argument
    """Repairs broken references.  Using -f markdown+autolink_bare_uris
    splits braced references like {@label:id} at the ':' into Link and Str
    elements.  This function replaces the mess with the Cite and Str
    elements we normally expect.  Call this before any reference processing.
    """

    if key in ('Para', 'Plain'):
        _repair_refs(value)

#-----------------------------------------------------------------------------
# use_refs_factory()

def _is_ref(key, value, references):
    """True if Cite element is a reference; False otherwise.
    references - a list containing known references.
    """
    return key == 'Cite' and value[1][0]['c'][1:] in references

def _parse_ref(key, value):
    """Parses a reference.  Returns the label."""
    assert key == 'Cite'
    prefix = value[0][0]['citationPrefix']
    label = value[1][0]['c'][1:]
    suffix = value[0][0]['citationSuffix']
    return prefix, label, suffix

def use_refs_factory(references):
    """Processing references like {+@eq:einstein} can be difficult.  We need
    an action -- call it use_refs() -- that we can apply to a document to
    parse the json and substitute Ref elements instead.  Ref elements aren't
    understood by pandoc, but are easily identified and processed by a filter.

    This factory function returns a function that substitutes Ref elements
    for the given references.  Note that all Ref elements must be removed
    before the json is output.
    """

    # pylint: disable=unused-argument
    def use_refs_action(key, value, fmt, meta):
        """Replaces known references with Ref elements."""

        def _process_modifier(value, i, attrs):
            """Trims +/- in front of reference and adds cref attribute.
            Sets empty values to None."""
            if value[i-1]['t'] == 'Str':
                flag = False  # Flags that a modifier was found
                if value[i-1]['c'].endswith('+'):
                    attrs[2].append(['cref', 'On'])
                    flag = True
                elif value[i-1]['c'].endswith('-'):
                    attrs[2].append(['cref', 'Off'])
                    flag = True
                if flag:  # Trim off the modifier
                    if len(value[i-1]['c']) > 1:
                        value[i-1]['c'] = value[i-1]['c'][:-1]
                    else:
                        value[i-1] = None

        def _remove_brackets(value, i):
            """Removes curly brackets surrounding value at index i.  Sets
            empty values to None.
            """
            # Check to see if the surrounding elements are strings
            if value[i-1] is None or value[i+1] is None:
                return
            if not value[i-1]['t'] == value[i+1]['t'] == 'Str':
                return
            # Check for the curly brackets
            if value[i-1]['c'].endswith('{') and \
              value[i+1]['c'].startswith('}'):
                # Trim off the brackets and set empty values to None
                if len(value[i-1]['c']) > 1:
                    value[i-1]['c'] = value[i-1]['c'][:-1]
                else:
                    value[i-1] = None
                if len(value[i+1]['c']) > 1:
                    value[i+1]['c'] = value[i+1]['c'][1:]
                else:
                    value[i+1] = None

        @filter_null
        def _use_refs(value):
            """Extracts attributes appends them to the reference."""
            for i, v in enumerate(value):
                if v and _is_ref(v['t'], v['c'], references):

                    # Extract the attributes
                    attrs = ['', [], []]  # Initialized to empty
                    if i+1 < len(value):
                        try: # Look for attributes in { ... }
                            # extract_attrs() sets extracted values to None
                            # in the value list.
                            attrs = extract_attrs(value, i+1)
                        except AssertionError:
                            pass

                     # Process any +/- modifier
                    if i > 0:
                        _process_modifier(value, i, attrs)

                    # Remove surrounding brackets
                    if i > 0 and i+1 < len(value):
                        _remove_brackets(value, i)

                    # Insert the Ref element
                    value[i] = Ref(attrs, *_parse_ref(v['t'], v['c']))
                    value[i]['c'] = list(value[i]['c'])  # Needed for unit tests

        if key in ['Para', 'Plain']:
            _use_refs(value)

    return use_refs_action


#-----------------------------------------------------------------------------
# use_attrimages() and filter_attrimages() actions

def _extract_imageattrs(value, n):
    """Extracts attributes from a list of values.  n is the index of the image.
    Extracted elements are set to None in the value list.  Attrs are returned
    in pandoc format.
    """
    assert value[n]['t'] == 'Image'

    # Notes: No space between an image and its attributes;
    # extract_attrs() sets extracted values to None in the value list.
    try:
        return extract_attrs(value, n+1)
    except AssertionError:
        # Look for attributes attached to the image path, as occurs with
        # reference links.  Remove the encoding.
        image = value[n]
        try:
            seq = unquote(image['c'][1][0]).split()
            path, s = seq[0], ' '.join(seq[1:])
        except ValueError:
            pass
        else:
            image['c'][1][0] = path  # Remove attr string from the path
            return PandocAttributes(s.strip(), 'markdown').to_pandoc()

def use_attrimages(key, value, fmt, meta):  # pylint: disable=unused-argument
    """Substitutes AttrImage elements for all attributed images (pandoc<1.16).
    AttrImage is the same as Image for pandoc>=1.16.  Unattributed images are
    left untouched.
    """

    @filter_null
    def _use_attrimages(value):
        """Performs the substitution."""
        # Seach for attributed images and replace them with an AttrImage
        for i, v in enumerate(value):
            if v and v['t'] == 'Image':
                # Extracted values get set to None in values list
                attrs = _extract_imageattrs(value, i)
                if attrs:
                    value[i] = AttrImage(attrs, *v['c'])
                    value[i]['c'] = list(value[i]['c'])  # Needed for unit tests

    if PANDOCVERSION < '1.16' and (key == 'Para' or key == 'Plain'):
        _use_attrimages(value)
        # Add the figure marker
        if len(value) == 1 and value[0]['t'] == 'Image' and \
          len(value[0]['c']) == 3:
            value[0]['c'][2][1] = 'fig:'  # Pandoc uses this as a figure marker

def filter_attrimages(key, value, fmt, meta):  # pylint: disable=unused-argument
    """Replaces all AttrImage elements with Image elements (pandoc<1.16)."""
    if PANDOCVERSION < '1.16' and key == 'Image' and len(value) == 3:
        image = elt('Image', 2)(*value[1:])
        image['c'] = list(image['c'])  # Needed for unit tests
        return image


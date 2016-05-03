#! /usr/bin/env python3

"""Unit tests for pandocfiltering."""

# Copyright 2016 Thomas J. Duck.
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

import sys
import unittest

from pandocfiltering import quotify, dollarfy, pandocify
from pandocfiltering import extract_attrs, repair_refs, filter_null

PANDOCVERSION = '1.17.0.2'  # Version for the testing

#-----------------------------------------------------------------------------
# Documents and expected results after processing.

# pylint: disable=line-too-long, eval-used

# Markdown: "test"
INPUT1 = eval(r'''[{"c": [{"c": [{"c": [], "t": "DoubleQuote"}, [{"c": "test", "t": "Str"}]], "t": "Quoted"}], "t": "Para"}]''')
EXPECTED1 = eval(r'''[{"c": [{"c": "\"test\"", "t": "Str"}], "t": "Para"}]''')

# Markdown: This is 'test 2'.
INPUT2 = eval(r'''[{"c": [{"c": "This", "t": "Str"}, {"c": [], "t": "Space"}, {"c": "is", "t": "Str"}, {"c": [], "t": "Space"}, {"c": [{"c": [], "t": "SingleQuote"}, [{"c": "test", "t": "Str"}, {"c": [], "t": "Space"}, {"c": "2", "t": "Str"}]], "t": "Quoted"}, {"c": ".", "t": "Str"}], "t": "Para"}]''')
EXPECTED2 = eval(r'''[{"t": "Para", "c": [{"t": "Str", "c": "This"}, {"t": "Space", "c": []}, {"t": "Str", "c": "is"}, {"t": "Space", "c": []}, {"t": "Str", "c": "'test"}, {"t": "Space", "c": []}, {"t": "Str", "c": "2'."}]}]''')

# Markdown: $\frac{1}{2}$
INPUT3 = eval(r'''[{"t": "Para", "c": [{"t": "Math", "c": [{"t": "InlineMath", "c": []}, "\\frac{1}{2}"]}]}]''')
EXPECTED3 = eval(r'''[{"t": "Para", "c": [{"t": "Str", "c": "$\\frac{1}{2}$"}]}]''')

# Markdown: This is a test.
INPUT4 = 'This is a test.'
EXPECTED4 = eval(r'''[{"t":"Str","c":"This"},{"t":"Space","c":[]},{"t":"Str","c":"is"},{"t":"Space","c":[]},{"t":"Str","c":"a"},{"t":"Space","c":[]},{"t":"Str","c":"test."}]''')

# Markdown: Test {#eq:id .class tag="foo"}.
INPUT5 = eval(r'''[{"t": "Str", "c": "Test"}, {"t": "Space", "c": []}, {"t": "Str", "c": "{#eq:id"}, {"t": "Space", "c": []}, {"t": "Str", "c": ".class"}, {"t": "Space", "c": []}, {"t": "Str", "c": "tag=\"foo\"}."}]''')
EXPECTED5 = ['eq:id', ['class'], [['tag', 'foo']]]

# Markdown: Test {#eq:id .class tag="foo"}.
INPUT6 = eval(r'''[{"c": "Test", "t": "Str"}, {"c": [], "t": "Space"}, {"c": "{#eq:id", "t": "Str"}, {"c": [], "t": "Space"}, {"c": ".class", "t": "Str"}, {"c": [], "t": "Space"}, {"c": "tag=", "t": "Str"}, {"c": [{"c": [], "t": "DoubleQuote"}, [{"c": "foo", "t": "Str"}]], "t": "Quoted"}, {"c": "}.", "t": "Str"}]''')
EXPECTED6 = EXPECTED5

# Markdown: {@doe:1999}
INPUT7 = eval(r'''[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@doe"}],["mailto:%7B@doe",""]]},{"t":"Str","c":":1999}"}]''')
EXPECTED7 = eval(r'''[{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"doe:1999","citationHash":0}],[{"t":"Str","c":"@doe:1999"}]]},{"t":"Str","c":"}"}]''')

# Markdown: Eqs. {@eq:1}a and {@eq:1}b.
INPUT8 = eval(r'''[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@eq"}],["mailto:%7B@eq",""]]},{"t":"Str","c":":1}a"},{"t":"Space","c":[]},{"t":"Str","c":"and"},{"t":"Space","c":[]},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@eq"}],["mailto:%7B@eq",""]]},{"t":"Str","c":":1}b"}]''')
EXPECTED8 = eval(r'''[{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"}a"},{"t":"Space","c":[]},{"t":"Str","c":"and"},{"t":"Space","c":[]},{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"}b"}]''')


#-----------------------------------------------------------------------------
# Test class

class TestModule(unittest.TestCase):
    """Test the pandocfiltering module."""

    def test_quotify(self):
        """Tests quotify()."""
        self.assertEqual(quotify(INPUT1), EXPECTED1)
        self.assertEqual(quotify(INPUT2), EXPECTED2)

    def test_dollarfy(self):
        """Tests dollarfy()."""
        self.assertEqual(dollarfy(INPUT3), EXPECTED3)

    def test_pandocify(self):
        """Tests pandocify()."""
        self.assertEqual(pandocify(INPUT4), EXPECTED4)

    def test_extract_attrs(self):
        """Tests extract_attrs()."""
        self.assertEqual(filter_null(extract_attrs)(INPUT5, 2), EXPECTED5)
        self.assertEqual(filter_null(extract_attrs)(INPUT6, 2), EXPECTED6)

    def test_repair_refs(self):
        """Tests repair_refs()."""
        self.assertEqual(repair_refs(INPUT7, pandocversion=PANDOCVERSION),
                         EXPECTED7)
        self.assertEqual(repair_refs(INPUT8, pandocversion=PANDOCVERSION),
                         EXPECTED8)


#-----------------------------------------------------------------------------
# main()

def main():
    """Runs the suite of unit tests"""

    # Do the tests
    suite = unittest.makeSuite(TestModule)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    n_errors = len(result.errors)
    n_failures = len(result.failures)

    if n_errors or n_failures:
        print('\n\nSummary: %d errors and %d failures reported\n'%\
            (n_errors, n_failures))

    print()

    sys.exit(n_errors+n_failures)


if __name__ == '__main__':
    main()()

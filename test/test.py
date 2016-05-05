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

from pandocfilters import walk

import pandocfiltering
from pandocfiltering import quotify, dollarfy, pandocify
from pandocfiltering import extract_attrs, repair_refs, filter_null
from pandocfiltering import use_attrimages, filter_attrimages
from pandocfiltering import use_refs_factory

pandocfiltering.init('1.17.0.2')

#-----------------------------------------------------------------------------
# Documents and expected results after processing.

# pylint: disable=line-too-long, eval-used


# Markdown (pandoc 1.16):

#-----------------------------------------------------------------------------
# Test class

class TestModule(unittest.TestCase):
    """Test the pandocfiltering module."""

    def test_quotify(self):
        """Tests quotify()."""

        # test.md: "test"

        # Command: pandoc test.md --filter savejson.py -o test.tex
        src = eval(r'''[{"c": [{"c": [{"c": [], "t": "DoubleQuote"}, [{"c": "test", "t": "Str"}]], "t": "Quoted"}], "t": "Para"}]''')

        # Command: pandoc test.md --filter savejson.py -o test.html
        expected = eval(r'''[{"c": [{"c": "\"test\"", "t": "Str"}], "t": "Para"}]''')

        self.assertEqual(quotify(src), expected)

        # test.md: This is 'test 2'.
        
        # Command: pandoc test.md --filter savejson.py -o test.tex
        src = eval(r'''[{"c": [{"c": "This", "t": "Str"}, {"c": [], "t": "Space"}, {"c": "is", "t": "Str"}, {"c": [], "t": "Space"}, {"c": [{"c": [], "t": "SingleQuote"}, [{"c": "test", "t": "Str"}, {"c": [], "t": "Space"}, {"c": "2", "t": "Str"}]], "t": "Quoted"}, {"c": ".", "t": "Str"}], "t": "Para"}]''')

        # Command: pandoc test.md --filter savejson.py -o test.html
        expected = eval(r'''[{"t": "Para", "c": [{"t": "Str", "c": "This"}, {"t": "Space", "c": []}, {"t": "Str", "c": "is"}, {"t": "Space", "c": []}, {"t": "Str", "c": "'test"}, {"t": "Space", "c": []}, {"t": "Str", "c": "2'."}]}]''')

        self.assertEqual(quotify(src), expected)


    def test_dollarfy(self):
        """Tests dollarfy()."""

        # test.md: $\frac{1}{2}$
        
        # Command: pandoc test.md -t json
        src = eval(r'''[{"t": "Math", "c": [{"t": "InlineMath", "c": []}, "\\frac{1}{2}"]}]''')

        # Hand-coded replacement
        expected = eval(r'''[{"t": "Str", "c": "$\\frac{1}{2}$"}]''')

        self.assertEqual(dollarfy(src), expected)


    def test_pandocify(self):
        """Tests pandocify()."""

        # test.md: This is a test.
        src = 'This is a test.'

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"t":"Str","c":"This"},{"t":"Space","c":[]},{"t":"Str","c":"is"},{"t":"Space","c":[]},{"t":"Str","c":"a"},{"t":"Space","c":[]},{"t":"Str","c":"test."}]''')

        self.assertEqual(pandocify(src), expected)


    def test_extract_attrs(self):
        """Tests extract_attrs()."""

        # test.md: Test {#eq:id .class tag="foo"}.

        # Command: pandoc test.md -filter savejson.py -o test.html
        src = eval(r'''[{"t": "Str", "c": "Test"}, {"t": "Space", "c": []}, {"t": "Str", "c": "{#eq:id"}, {"t": "Space", "c": []}, {"t": "Str", "c": ".class"}, {"t": "Space", "c": []}, {"t": "Str", "c": "tag=\"foo\"}."}]''')

        # Hand-coded
        expected = ['eq:id', ['class'], [['tag', 'foo']]]

        self.assertEqual(filter_null(extract_attrs)(src, 2), expected)

        # Command: pandoc test.md -filter savejson.py -o test.tex
        src = eval(r'''[{"c": "Test", "t": "Str"}, {"c": [], "t": "Space"}, {"c": "{#eq:id", "t": "Str"}, {"c": [], "t": "Space"}, {"c": ".class", "t": "Str"}, {"c": [], "t": "Space"}, {"c": "tag=", "t": "Str"}, {"c": [{"c": [], "t": "DoubleQuote"}, [{"c": "foo", "t": "Str"}]], "t": "Quoted"}, {"c": "}.", "t": "Str"}]''')

        self.assertEqual(filter_null(extract_attrs)(src, 2), expected)


    def test_repair_refs(self):
        """Tests repair_refs()."""

        # test.md: {@doe:1999}

        # Command: pandoc test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@doe"}],["mailto:%7B@doe",""]]},{"t":"Str","c":":1999}"}]}]]''')

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"doe:1999","citationHash":0}],[{"t":"Str","c":"@doe:1999"}]]},{"t":"Str","c":"}"}]}]]''')

        self.assertEqual(walk(src, repair_refs, '', {}), expected)

        # test.md: Eqs. {@eq:1}a and {@eq:1}b.

        # Command: pandoc test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"Eqs."},{"t":"Space","c":[]},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@eq"}],["mailto:%7B@eq",""]]},{"t":"Str","c":":1}a"},{"t":"Space","c":[]},{"t":"Str","c":"and"},{"t":"Space","c":[]},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@eq"}],["mailto:%7B@eq",""]]},{"t":"Str","c":":1}b."}]}]]''')

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"Eqs."},{"t":"Space","c":[]},{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"}a"},{"t":"Space","c":[]},{"t":"Str","c":"and"},{"t":"Space","c":[]},{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"}b."}]}]]''')

        self.assertEqual(walk(src, repair_refs, {}, ''), expected)

        # test.md: See {+@eq:1}.

        # Command: pandoc test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{+@eq"}],["mailto:%7B+@eq",""]]},{"t":"Str","c":":1}."}]}]]''')

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Str","c":"{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"}."}]}]]''')

        self.assertEqual(walk(src, repair_refs, {}, ''), expected)

        # test.md: *@fig:plot1 and {+@fig:plot3}a.
        
        # Command: pandoc test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"*@fig"}],["mailto:*@fig",""]]},{"t":"Str","c":":plot1"},{"t":"Space","c":[]},{"t":"Str","c":"and"},{"t":"Space","c":[]},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{+@fig"}],["mailto:%7B+@fig",""]]},{"t":"Str","c":":plot3}a."}]}]]''')

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"*"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:plot1","citationHash":0}],[{"t":"Str","c":"@fig:plot1"}]]},{"t":"Space","c":[]},{"t":"Str","c":"and"},{"t":"Space","c":[]},{"t":"Str","c":"{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:plot3","citationHash":0}],[{"t":"Str","c":"@fig:plot3"}]]},{"t":"Str","c":"}a."}]}]]''')

        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


    def test_use_attrimage(self):
        """Tests use_attrimage()."""

        # test.md: ![Caption](img.png){#fig:id}

        # Command: pandoc-1.15.2 test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Image","c":[[{"t":"Str","c":"Caption"}],["img.png",""]]},{"t":"Str","c":"{#fig:id}"}]}]]''')

        # Command: pandoc-1.17.0.2 test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Image","c":[["fig:id",[],[]],[{"t":"Str","c":"Caption"}],["img.png","fig:"]]}]}]]''')

        pandocfiltering.init('1.15.0.2')
        self.assertEqual(walk(src, use_attrimages, '', {}), expected)
        pandocfiltering.init('1.17.0.2')


    def test_filter_attrimage(self):
        """Tests filter_attrimage()."""

        # test.md: ![Caption](img.png){#fig:id}

        # Command: pandoc-1.17.0.2 test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Image","c":[["fig:id",[],[]],[{"t":"Str","c":"Caption"}],["img.png","fig:"]]}]}]]''')

        # Hand-coded
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Image","c":[[{"t":"Str","c":"Caption"}],["img.png","fig:"]]}]}]]''')

        pandocfiltering.init('1.15.2')
        self.assertEqual(walk(src, filter_attrimages, '', {}), expected)
        pandocfiltering.init('1.17.0.2')


    def test_use_refs_factory(self):
        """Tests use_refs_factory()."""

        # test.md: As shown in @fig:one.

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"As"},{"t":"Space","c":[]},{"t":"Str","c":"shown"},{"t":"Space","c":[]},{"t":"Str","c":"in"},{"t":"Space","c":[]},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:one","citationHash":0}],[{"t":"Str","c":"@fig:one"}]]},{"t":"Str","c":"."}]}]]''')

        # Hand-coded
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"As"},{"t":"Space","c":[]},{"t":"Str","c":"shown"},{"t":"Space","c":[]},{"t":"Str","c":"in"},{"t":"Space","c":[]},{"t":"Ref","c":[['',[],[]],'fig:one']},{"t":"Str","c":"."}]}]]''')

        use_refs = use_refs_factory(['fig:one'])
        self.assertEqual(walk(src, use_refs, '', {}), expected)
        
        # test.md: See {+@eq:1}.

        # Command: pandoc test.md -t json
        src = [{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Str","c":"{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"}."}]}]]

        # Hand-coded
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Ref","c":[["",[],[["modifier","+"]]],"eq:1"]},{"t":"Str","c":"."}]}]]''')

        use_refs = use_refs_factory(['eq:1'])
        self.assertEqual(walk(src, use_refs, '', {}), expected)

        # test.md: {+@tbl:one{.test}}-{@tbl:four} provide the data.

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"tbl:one","citationHash":0}],[{"t":"Str","c":"@tbl:one"}]]},{"t":"Str","c":"{.test}}-{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"tbl:four","citationHash":0}],[{"t":"Str","c":"@tbl:four"}]]},{"t":"Str","c":"}"},{"t":"Space","c":[]},{"t":"Str","c":"provide"},{"t":"Space","c":[]},{"t":"Str","c":"the"},{"t":"Space","c":[]},{"t":"Str","c":"data."}]}]]''')

        # Hand-coded
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Ref","c":[['',['test'],[["modifier","+"]]],"tbl:one"]},{"t":"Str","c":"-"},{"t":"Ref","c":[['',[],[]],"tbl:four"]},{"t":"Space","c":[]},{"t":"Str","c":"provide"},{"t":"Space","c":[]},{"t":"Str","c":"the"},{"t":"Space","c":[]},{"t":"Str","c":"data."}]}]]''')

        use_refs = use_refs_factory(['tbl:one', 'tbl:four'])
        output = walk(src, use_refs, '', {})
        self.assertEqual(output, expected)


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

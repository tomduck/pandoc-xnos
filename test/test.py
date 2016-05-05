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
import subprocess

from pandocfilters import walk

import pandocfiltering
from pandocfiltering import quotify, dollarfy, pandocify
from pandocfiltering import extract_attrs, repair_refs, filter_null
from pandocfiltering import use_attrimages, filter_attrimages
from pandocfiltering import use_refs_factory

PANDOCVERSION = '1.17.0.1'

pandocfiltering.init(PANDOCVERSION)

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

        ## test.md: "test" ##
        
        # Command: pandoc test.md --smart -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Quoted","c":[{"t":"DoubleQuote","c":[]},[{"t":"Str","c":"test"}]]}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '"test"'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc --smart -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"\"test\""}]}]]''')

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', '"test"'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(quotify(src[1]), expected[1])

        
        ## test.md: This is 'test 2'. ##
        
        # Command: pandoc test.md --smart -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"This"},{"t":"Space","c":[]},{"t":"Str","c":"is"},{"t":"Space","c":[]},{"t":"Quoted","c":[{"t":"SingleQuote","c":[]},[{"t":"Str","c":"test"},{"t":"Space","c":[]},{"t":"Str","c":"2"}]]},{"t":"Str","c":"."}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', "This is 'test 2'."),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc --smart -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"This"},{"t":"Space","c":[]},{"t":"Str","c":"is"},{"t":"Space","c":[]},{"t":"Str","c":"'test"},{"t":"Space","c":[]},{"t":"Str","c":"2'."}]}]]''')

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', "This is 'test 2'."),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(quotify(src[1]), expected[1])


    def test_dollarfy(self):
        """Tests dollarfy()."""

        ## test.md: $\frac{1}{2}$ ##
        
        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Math","c":[{"t":"InlineMath","c":[]},"\\frac{1}{2}"]}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', r'$\frac{1}{2}$'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded
        expected = eval(r'''[{"t": "Str", "c": "$\\frac{1}{2}$"}]''')

        # Make the comparison
        self.assertEqual(dollarfy(src[1][0]['c']), expected)


    def test_pandocify(self):
        """Tests pandocify()."""

        ## test.md: This is a test. ##

        src = 'This is a test.'

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"This"},{"t":"Space","c":[]},{"t":"Str","c":"is"},{"t":"Space","c":[]},{"t":"Str","c":"a"},{"t":"Space","c":[]},{"t":"Str","c":"test."}]}]]''')

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', 'This is a test.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(pandocify(src), expected[1][0]['c'])


    def test_extract_attrs(self):
        """Tests extract_attrs()."""

        ## test.md: Test {#eq:id .class tag="foo"}. ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"Test"},{"t":"Space","c":[]},{"t":"Str","c":"{#eq:id"},{"t":"Space","c":[]},{"t":"Str","c":".class"},{"t":"Space","c":[]},{"t":"Str","c":"tag=\"foo\"}."}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'Test {#eq:id .class tag="foo"}.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded
        expected = ['eq:id', ['class'], [['tag', 'foo']]]

        # Make the comparison
        self.assertEqual(filter_null(extract_attrs)(src[1][0]['c'], 2),
                         expected)

        
        ## Same test.md ##
        
        # Command: pandoc test.md --smart -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"Test"},{"t":"Space","c":[]},{"t":"Str","c":"{#eq:id"},{"t":"Space","c":[]},{"t":"Str","c":".class"},{"t":"Space","c":[]},{"t":"Str","c":"tag="},{"t":"Quoted","c":[{"t":"DoubleQuote","c":[]},[{"t":"Str","c":"foo"}]]},{"t":"Str","c":"}."}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'Test {#eq:id .class tag="foo"}.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc --smart -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Make the comparison
        self.assertEqual(filter_null(extract_attrs)(src[1][0]['c'], 2),
                         expected)


    def test_repair_refs(self):
        """Tests repair_refs()."""

        ## test.md: {@doe:1999} ##

        # Command: pandoc test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@doe"}],["mailto:%7B@doe",""]]},{"t":"Str","c":":1999}"}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '{@doe:1999}'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -f markdown+autolink_bare_uris -t json'.split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"doe:1999","citationHash":0}],[{"t":"Str","c":"@doe:1999"}]]},{"t":"Str","c":"}"}]}]]''')

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', '{@doe:1999}'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(walk(src, repair_refs, '', {}), expected)


        ## test.md: Eqs. {@eq:1}a and {@eq:1}b. ##

        # Command: pandoc test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"Eqs."},{"t":"Space","c":[]},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@eq"}],["mailto:%7B@eq",""]]},{"t":"Str","c":":1}a"},{"t":"Space","c":[]},{"t":"Str","c":"and"},{"t":"Space","c":[]},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@eq"}],["mailto:%7B@eq",""]]},{"t":"Str","c":":1}b."}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'Eqs. {@eq:1}a and {@eq:1}b.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -f markdown+autolink_bare_uris -t json'.split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"Eqs."},{"t":"Space","c":[]},{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"}a"},{"t":"Space","c":[]},{"t":"Str","c":"and"},{"t":"Space","c":[]},{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"}b."}]}]]''')

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', 'Eqs. {@eq:1}a and {@eq:1}b.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


        ## test.md: See {+@eq:1}. ##

        # Command: pandoc test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{+@eq"}],["mailto:%7B+@eq",""]]},{"t":"Str","c":":1}."}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'See {+@eq:1}.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -f markdown+autolink_bare_uris -t json'.split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Str","c":"{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"}."}]}]]''')

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', 'See {+@eq:1}.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


        ## test.md: *@fig:plot1 and {+@fig:plot3}a. ##
        
        # Command: pandoc test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"*@fig"}],["mailto:*@fig",""]]},{"t":"Str","c":":plot1"},{"t":"Space","c":[]},{"t":"Str","c":"and"},{"t":"Space","c":[]},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{+@fig"}],["mailto:%7B+@fig",""]]},{"t":"Str","c":":plot3}a."}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '*@fig:plot1 and {+@fig:plot3}a.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -f markdown+autolink_bare_uris -t json'.split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"*"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:plot1","citationHash":0}],[{"t":"Str","c":"@fig:plot1"}]]},{"t":"Space","c":[]},{"t":"Str","c":"and"},{"t":"Space","c":[]},{"t":"Str","c":"{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:plot3","citationHash":0}],[{"t":"Str","c":"@fig:plot3"}]]},{"t":"Str","c":"}a."}]}]]''')

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', '*@fig:plot1 and {+@fig:plot3}a.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


    def test_use_attrimage(self):
        """Tests use_attrimage()."""

        ## test.md: ![Caption](img.png){#fig:id} ##

        # Command: pandoc-1.15.2 test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Image","c":[[{"t":"Str","c":"Caption"}],["img.png",""]]},{"t":"Str","c":"{#fig:id}"}]}]]''')

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Image","c":[["fig:id",[],[]],[{"t":"Str","c":"Caption"}],["img.png","fig:"]]}]}]]''')

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', '![Caption](img.png){#fig:id}'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        pandocfiltering.init('1.15.0.2')
        self.assertEqual(walk(src, use_attrimages, '', {}), expected)
        pandocfiltering.init(PANDOCVERSION)


    def test_filter_attrimage(self):
        """Tests filter_attrimage()."""

        ## test.md: ![Caption](img.png){#fig:id} ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Image","c":[["fig:id",[],[]],[{"t":"Str","c":"Caption"}],["img.png","fig:"]]}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '![Caption](img.png){#fig:id}'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -f markdown+autolink_bare_uris -t json'.split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (attributes deleted)
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Image","c":[[{"t":"Str","c":"Caption"}],["img.png","fig:"]]}]}]]''')

        # Make the comparison
        pandocfiltering.init('1.15.2')
        self.assertEqual(walk(src, filter_attrimages, '', {}), expected)
        pandocfiltering.init(PANDOCVERSION)


    def test_use_refs_factory(self):
        """Tests use_refs_factory()."""

        ## test.md: As shown in @fig:one. ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"As"},{"t":"Space","c":[]},{"t":"Str","c":"shown"},{"t":"Space","c":[]},{"t":"Str","c":"in"},{"t":"Space","c":[]},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:one","citationHash":0}],[{"t":"Str","c":"@fig:one"}]]},{"t":"Str","c":"."}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'As shown in @fig:one.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (Ref inserted)
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"As"},{"t":"Space","c":[]},{"t":"Str","c":"shown"},{"t":"Space","c":[]},{"t":"Str","c":"in"},{"t":"Space","c":[]},{"t":"Ref","c":[['',[],[]],'fig:one']},{"t":"Str","c":"."}]}]]''')

        # Make the comparison
        use_refs = use_refs_factory(['fig:one'])
        self.assertEqual(walk(src, use_refs, '', {}), expected)


        ## test.md: See {+@eq:1}. ##

        # Command: pandoc test.md -t json
        src = [{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Str","c":"{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"}."}]}]]

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'See {+@eq:1}.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (Ref inserted)
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Ref","c":[["",[],[["modifier","+"]]],"eq:1"]},{"t":"Str","c":"."}]}]]''')

        # Make the comparison
        use_refs = use_refs_factory(['eq:1'])
        self.assertEqual(walk(src, use_refs, '', {}), expected)


        ## test.md: {+@tbl:one{.test}}-{@tbl:four} provide the data. ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"tbl:one","citationHash":0}],[{"t":"Str","c":"@tbl:one"}]]},{"t":"Str","c":"{.test}}-{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"tbl:four","citationHash":0}],[{"t":"Str","c":"@tbl:four"}]]},{"t":"Str","c":"}"},{"t":"Space","c":[]},{"t":"Str","c":"provide"},{"t":"Space","c":[]},{"t":"Str","c":"the"},{"t":"Space","c":[]},{"t":"Str","c":"data."}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(
            ('echo', '{+@tbl:one{.test}}-{@tbl:four} provide the data.'),
            stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)
        
        # Hand-coded (ref inserted)
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Ref","c":[['',['test'],[["modifier","+"]]],"tbl:one"]},{"t":"Str","c":"-"},{"t":"Ref","c":[['',[],[]],"tbl:four"]},{"t":"Space","c":[]},{"t":"Str","c":"provide"},{"t":"Space","c":[]},{"t":"Str","c":"the"},{"t":"Space","c":[]},{"t":"Str","c":"data."}]}]]''')

        # Make the comparison
        use_refs = use_refs_factory(['tbl:one', 'tbl:four'])
        self.assertEqual(walk(src, use_refs, '', {}), expected)


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

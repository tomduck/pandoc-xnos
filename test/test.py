#! /usr/bin/env python3

"""Unit tests for pandoc-xnos."""

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

# pylint: disable=eval-used, line-too-long

import sys
import unittest
import subprocess

from pandocfilters import walk, Math

import pandocxnos
from pandocxnos import get_meta
from pandocxnos import join_strings
from pandocxnos import quotify, dollarfy
from pandocxnos import extract_attrs
from pandocxnos import attach_attrs_factory, detach_attrs_factory
from pandocxnos import repair_refs, process_refs_factory, replace_refs_factory

PANDOCVERSION = '1.17.0.2'

pandocxnos.init(PANDOCVERSION)


#-----------------------------------------------------------------------------
# Test class

# pylint: disable=too-many-public-methods
class TestModule(unittest.TestCase):
    """Test the pandocxnos package."""

    def test_get_meta_1(self):
        """Tests get_meta() #1."""

        ## test.md empty

        # Command: pandoc test.md -t json -M foo=bar
        src = eval(r'''[{"unMeta":{"foo":{"t":"MetaString","c":"bar"}}},[]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', ''), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json -M foo=bar'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        expected = 'bar'

        # Make the comparison
        self.assertEqual(get_meta(src[0]['unMeta'], 'foo'), expected)


    def test_get_meta_2(self):
        """Tests get_meta() #2."""

        ## test.md: ---\nfoo: bar\n... ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{"foo":{"t":"MetaInlines","c":[{"t":"Str","c":"bar"}]}}},[]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '---\nfoo: bar\n...'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        expected = 'bar'

        # Make the comparison
        self.assertEqual(get_meta(src[0]['unMeta'], 'foo'), expected)


    def test_get_meta_3(self):
        """Tests get_meta() #3."""

        ## test.md: ---\nfoo:\n  - bar\n  - baz\n... ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{"foo":{"t":"MetaList","c":[{"t":"MetaInlines","c":[{"t":"Str","c":"bar"}]},{"t":"MetaInlines","c":[{"t":"Str","c":"baz"}]}]}}},[]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '---\nfoo:\n  - bar\n  - baz\n...'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        expected = ['bar', 'baz']

        # Make the comparison
        self.assertEqual(get_meta(src[0]['unMeta'], 'foo'), expected)


    def test_get_meta_4(self):
        """Tests get_meta() #4."""

        ## test.md: ---\nfoo: True\n... ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{"foo":{"t":"MetaBool","c":True}}},[]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '---\nfoo: True\n...'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip()\
            .decode("utf-8").replace('true', 'True'))
        self.assertEqual(src, output)

        expected = True

        # Make the comparison
        self.assertEqual(get_meta(src[0]['unMeta'], 'foo'), expected)


    def test_quotify_1(self):
        """Tests quotify() #1."""

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


    def test_quotify_2(self):
        """Tests quotify() #2."""

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


    def test_extract_attrs_1(self):
        """Tests extract_attrs() #1."""

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
        self.assertEqual(extract_attrs(src[1][0]['c'], 2), expected)


    def test_extract_attrs_2(self):
        """Tests extract_attrs() #2."""

        ## test.md: Test {#eq:id .class tag="foo"}. ##

        # Command: pandoc test.md --smart -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"Test"},{"t":"Space","c":[]},{"t":"Str","c":"{#eq:id"},{"t":"Space","c":[]},{"t":"Str","c":".class"},{"t":"Space","c":[]},{"t":"Str","c":"tag="},{"t":"Quoted","c":[{"t":"DoubleQuote","c":[]},[{"t":"Str","c":"foo"}]]},{"t":"Str","c":"}."}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'Test {#eq:id .class tag="foo"}.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc --smart -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded
        expected = ['eq:id', ['class'], [['tag', 'foo']]]

        # Make the comparison
        self.assertEqual(extract_attrs(src[1][0]['c'], 2), expected)


    def test_repair_refs_1(self):
        """Tests repair_refs() #1."""

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


    def test_repair_refs_2(self):
        """Tests repair_refs() #2."""

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


    def test_repair_refs_3(self):
        """Tests repair_refs() #3."""

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


    def test_repair_refs_4(self):
        """Tests repair_refs() #4."""

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


    def test_repair_refs_5(self):
        """Tests repair_refs() #5."""

        ## test.md: +@eq:1, ##

        # Command: pandoc test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"+@eq"}],["mailto:+@eq",""]]},{"t":"Str","c":":1,"}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '+@eq:1,'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -f markdown+autolink_bare_uris -t json'.split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":","}]}]]''')

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', '+@eq:1,'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


    def test_repair_refs_6(self):
        """Tests repair_refs() #6."""

        ## test.md: {@fig:1{baz=bat}}a ##

        # Command: pandoc test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@fig"}],["mailto:%7B@fig",""]]},{"t":"Str","c":":1{baz=bat}}a"}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '{@fig:1{baz=bat}}a'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -f markdown+autolink_bare_uris -t json'.split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:1","citationHash":0}],[{"t":"Str","c":"@fig:1"}]]},{"t":"Str","c":"{baz=bat}}a"}]}]]''')

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', '{@fig:1{baz=bat}}a'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


    def test_repair_refs_7(self):
        """Tests repair_refs() #7."""

        ## test.md: {@fig:1{baz=bat foo=bar}}a ##

        # Command: pandoc test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@fig"}],["mailto:%7B@fig",""]]},{"t":"Str","c":":1{baz=bat"},{"t":"Space","c":[]},{"t":"Str","c":"foo=bar}}a"}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '{@fig:1{baz=bat foo=bar}}a'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -f markdown+autolink_bare_uris -t json'.split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:1","citationHash":0}],[{"t":"Str","c":"@fig:1"}]]},{"t":"Str","c":"{baz=bat"},{"t":"Space","c":[]},{"t":"Str","c":"foo=bar}}a"}]}]]''')

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', '{@fig:1{baz=bat foo=bar}}a'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


    def test_repair_refs_8(self):
        """Tests repair_refs() #8."""

        ## test.md: {@fig:1}-{@fig:3} ##

        # Command: pandoc test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@fig"}],["mailto:%7B@fig",""]]},{"t":"Str","c":":"},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"1}-{@fig"}],["mailto:1%7D-%7B@fig",""]]},{"t":"Str","c":":3}"}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '{@fig:1}-{@fig:3}'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -f markdown+autolink_bare_uris -t json'.split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:1","citationHash":0}],[{"t":"Str","c":"@fig:1"}]]},{"t":"Str","c":"}-{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:3","citationHash":0}],[{"t":"Str","c":"@fig:3"}]]},{"t":"Str","c":"}"}]}]]''')

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', '{@fig:1}-{@fig:3}'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


    def test_process_refs_factory_1(self):
        """Tests process_refs_factory() #1."""

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

        # Hand-coded (added empty attributes)
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"As"},{"t":"Space","c":[]},{"t":"Str","c":"shown"},{"t":"Space","c":[]},{"t":"Str","c":"in"},{"t":"Space","c":[]},{"t":"Cite","c":[["",[],[]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:one","citationHash":0}],[{"t":"Str","c":"@fig:one"}]]},{"t":"Str","c":"."}]}]]''')

        # Make the comparison
        process_refs = process_refs_factory(['fig:one'])
        self.assertEqual(walk(src, process_refs, '', {}), expected)

    def test_process_refs_factory_2(self):
        """Tests process_refs_factory() #2."""

        ## test.md: (@eq:one) ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"("},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:one","citationHash":0}],[{"t":"Str","c":"@eq:one"}]]},{"t":"Str","c":")"}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '(@eq:one)'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (no change)
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"("},{"t":"Cite","c":[["",[],[]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:one","citationHash":0}],[{"t":"Str","c":"@eq:one"}]]},{"t":"Str","c":")"}]}]]''')

        # Make the comparison
        process_refs = process_refs_factory(['eq:one'])
        self.assertEqual(walk(src, process_refs, '', {}), expected)


    def test_process_refs_factory_3(self):
        """Tests process_refs_factory() #3."""

        ## test.md: See {@tbl:1}. ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"tbl:1","citationHash":0}],[{"t":"Str","c":"@tbl:1"}]]},{"t":"Str","c":"}."}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'See {@tbl:1}.'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (braces stripped, attributes added)
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Cite","c":[["",[],[]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"tbl:1","citationHash":0}],[{"t":"Str","c":"@tbl:1"}]]},{"t":"Str","c":"."}]}]]''')

        # Make the comparison
        process_refs = process_refs_factory(['tbl:1'])
        self.assertEqual(walk(src, process_refs, '', {}), expected)


    def test_process_refs_factory_4(self):
        """Tests process_refs_factory() #4."""

        ## test.md: See +@eq:1. ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Str","c":"+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"."}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'See +@eq:1.'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (modifier extracted, attributes added)
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Cite","c":[["",[],[["modifier","+"]]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"."}]}]]''')

        # Make the comparison
        process_refs = process_refs_factory(['eq:1'])
        self.assertEqual(walk(src, process_refs, '', {}), expected)


    def test_process_refs_factory_5(self):
        """Tests process_refs_factory() #5."""

        ## test.md: See {+@tbl:1}. ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Str","c":"{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"tbl:1","citationHash":0}],[{"t":"Str","c":"@tbl:1"}]]},{"t":"Str","c":"}."}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'See {+@tbl:1}.'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (braces stripped, modifier extracted, attributes added)
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Cite","c":[["",[],[["modifier","+"]]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"tbl:1","citationHash":0}],[{"t":"Str","c":"@tbl:1"}]]},{"t":"Str","c":"."}]}]]''')

        # Make the comparison
        process_refs = process_refs_factory(['tbl:1'])
        self.assertEqual(walk(src, process_refs, '', {}), expected)


    def test_process_refs_factory_6(self):
        """Tests process_refs_factory() #6."""

        ## test.md: See xxx{+@tbl:1}xxx. ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Str","c":"xxx{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"tbl:1","citationHash":0}],[{"t":"Str","c":"@tbl:1"}]]},{"t":"Str","c":"}xxx."}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'See xxx{+@tbl:1}xxx.'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (braces stripped, modifier extracted, attributes added)
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Str","c":"xxx"},{"t":"Cite","c":[["",[],[["modifier","+"]]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"tbl:1","citationHash":0}],[{"t":"Str","c":"@tbl:1"}]]},{"t":"Str","c":"xxx."}]}]]''')

        # Make the comparison
        process_refs = process_refs_factory(['tbl:1'])
        self.assertEqual(walk(src, process_refs, '', {}), expected)


    def test_use_refs_factory_7(self):
        """Tests use_refs_factory() #7."""

        ## test.md: {+@tbl:one}-{@tbl:four} provide the data. ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"tbl:one","citationHash":0}],[{"t":"Str","c":"@tbl:one"}]]},{"t":"Str","c":"}-{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"tbl:four","citationHash":0}],[{"t":"Str","c":"@tbl:four"}]]},{"t":"Str","c":"}"},{"t":"Space","c":[]},{"t":"Str","c":"provide"},{"t":"Space","c":[]},{"t":"Str","c":"the"},{"t":"Space","c":[]},{"t":"Str","c":"data."}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(
            ('echo', '{+@tbl:one}-{@tbl:four} provide the data.'),
            stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Cite","c":[["",[],[["modifier","+"]]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"tbl:one","citationHash":0}],[{"t":"Str","c":"@tbl:one"}]]},{"t":"Str","c":"-"},{"t":"Cite","c":[["",[],[]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"tbl:four","citationHash":0}],[{"t":"Str","c":"@tbl:four"}]]},{"t":"Space","c":[]},{"t":"Str","c":"provide"},{"t":"Space","c":[]},{"t":"Str","c":"the"},{"t":"Space","c":[]},{"t":"Str","c":"data."}]}]]''')

        # Make the comparison
        process_refs = process_refs_factory(['tbl:one', 'tbl:four'])
        self.assertEqual(walk(src, process_refs, '', {}), expected)

    @unittest.skip('Known issue for pandoc-1.15.2')
    def test_use_refs_factory_8(self):
        """Tests use_refs_factory() #8."""

        ## test.md: @fig:1:

        # pandoc-1.15.2 doesn't detect references that end in a colon.  This
        # was fixed in subsequent versions of pandoc.  There is a trivial
        # workaround; use "{@fig:1}:" instead.  This is demonstrated in the
        # next unit test.  Given that there is a trivial work-around, this is
        # probably not worth fixing.

        # Command: pandoc-1.15.2 test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"@fig:1:"}]}]]''')

        # Check against pandoc-1.15.2
        md = subprocess.Popen(('echo', '@fig:1:'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc-1.15.2 -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Generate expected using current pandoc
        md = subprocess.Popen(('echo', '@fig:1:'), stdout=subprocess.PIPE)
        expected = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())

        # Make the comparison
        process_refs = process_refs_factory(['fig:1'])
        self.assertEqual(walk(src, process_refs, {}, ''), expected)


    def test_process_refs_factory_9(self):
        """Tests process_refs_factory() #9."""

        ## test.md: {@fig:1}:

        # See previous unit test

        # Command: pandoc-1.15.2 test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:1","citationHash":0}],[{"t":"Str","c":"@fig:1"}]]},{"t":"Str","c":"}:"}]}]]''')

        # Check against pandoc-1.15.2
        md = subprocess.Popen(('echo', '{@fig:1}:'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc-1.15.2 -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Cite","c":[["",[],[]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:1","citationHash":0}],[{"t":"Str","c":"@fig:1"}]]},{"t":"Str","c":":"}]}]]''')

        # Make the comparison
        process_refs = process_refs_factory(['fig:1'])
        self.assertEqual(walk(src, process_refs, {}, ''), expected)


    def test_replace_refs_factory(self):
        """Tests replace_refs_factory."""

        ## test.md: As shown in @fig:1. ##

        # Result from process_refs()
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"As"},{"t":"Space","c":[]},{"t":"Str","c":"shown"},{"t":"Space","c":[]},{"t":"Str","c":"in"},{"t":"Space","c":[]},{"t":"Cite","c":[["",[],[]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:one","citationHash":0}],[{"t":"Str","c":"@fig:one"}]]},{"t":"Str","c":"."}]}]]''')

        # Hand-coded
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"As"},{"t":"Space","c":[]},{"t":"Str","c":"shown"},{"t":"Space","c":[]},{"t":"Str","c":"in"},{"t":"Space","c":[]},{"t":"Str","c":"fig."},{"t":"Space","c":[]},{"t":"Str","c":"1."}]}]]''')

        # Make the comparison
        replace_refs = replace_refs_factory({'fig:one':1}, True,
                                            ['fig.', 'figs.'],
                                            ['Figure', 'Figures'],
                                            'figure')
        self.assertEqual(walk(walk(src, replace_refs, {}, ''),
                              join_strings, {}, ''), expected)


    def test_attach_attrs_factory(self):
        """Tests attach_attrs_math()."""

        attach_attrs_math = attach_attrs_factory(Math, allow_space=True)

        ## test.md: $$ y = f(x) $${#eq:1 tag="B.1"} ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Math","c":[{"t":"DisplayMath","c":[]}," y = f(x) "]},{"t":"Str","c":"{#eq:1"},{"t":"Space","c":[]},{"t":"Str","c":"tag=\"B.1\"}"}]}]]''')

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '$$ y = f(x) $${#eq:1 tag="B.1"}'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (attributes deleted)
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Math","c":[["eq:1",[],[["tag","B.1"]]],{"t":"DisplayMath","c":[]}," y = f(x) "]}]}]]''')

        # Make the comparison
        self.assertEqual(walk(src, attach_attrs_math, '', {}), expected)


    def test_detach_attrs_factory(self):
        """Tests filter_attrs_factory()."""

        detach_attrs_math = detach_attrs_factory(Math)

        ## Use expected result from _test_use_attrs_math() ##

        # Command: pandoc test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Math","c":[["eq:1",[],[["tag","B.1"]]],{"t":"DisplayMath","c":[]}," y = f(x) "]}]}]]''')

        # test.md: $$ y = f(x) $$

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Math","c":[{"t":"DisplayMath","c":[]}," y = f(x) "]}]}]]''')

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', '$$ y = f(x) $$'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            'pandoc -t json'.split(), stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(walk(src, detach_attrs_math, '', {}), expected)


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

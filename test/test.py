#! /usr/bin/env python3

"""Unit tests for pandoc-xnos."""

# Copyright 2016-2020 Thomas J. Duck.
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
from pandocxnos import PandocAttributes
from pandocxnos import get_meta, elt
from pandocxnos import join_strings
from pandocxnos import quotify, dollarfy
from pandocxnos import extract_attrs
from pandocxnos import attach_attrs_factory, detach_attrs_factory
from pandocxnos import insert_secnos_factory
from pandocxnos import repair_refs, process_refs_factory, replace_refs_factory

PANDOCVERSION = '2.8.1'
PANDOC = 'pandoc-2.10.1'
PANDOC1p15 = 'pandoc-1.15.2'  # pylint: disable=invalid-name
PANDOC_API_VERSION = '1,21'


#-----------------------------------------------------------------------------
# Test class

# pylint: disable=too-many-public-methods
class TestXnos(unittest.TestCase):
    """Test the pandocxnos package."""

    def setUp(self):
        """Sets up the test."""
        pandocxnos.init(PANDOCVERSION)

    def test_get_meta_1(self):
        """Tests get_meta() #1."""

        ## test.md empty

        # Command: pandoc test.md -t json -M foo=bar
        src = eval(r'''{"meta":{"foo":{"t":"MetaString","c":"bar"}},"blocks":[],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', ''), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json -M foo=bar').split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        expected = 'bar'

        # Make the comparison
        self.assertEqual(get_meta(src['meta'], 'foo'), expected)


    def test_get_meta_2(self):
        """Tests get_meta() #2."""

        ## test.md: ---\nfoo: bar\n... ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"meta":{"foo":{"t":"MetaInlines","c":[{"t":"Str","c":"bar"}]}},"blocks":[],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '---\nfoo: bar\n...'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        expected = 'bar'

        # Make the comparison
        self.assertEqual(get_meta(src['meta'], 'foo'), expected)


    def test_get_meta_3(self):
        """Tests get_meta() #3."""

        ## test.md: ---\nfoo:\n  - bar\n  - baz\n... ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"meta":{"foo":{"t":"MetaList","c":[{"t":"MetaInlines","c":[{"t":"Str","c":"bar"}]},{"t":"MetaInlines","c":[{"t":"Str","c":"baz"}]}]}},"blocks":[],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '---\nfoo:\n  - bar\n  - baz\n...'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        expected = ['bar', 'baz']

        # Make the comparison
        self.assertEqual(get_meta(src['meta'], 'foo'), expected)


    def test_get_meta_4(self):
        """Tests get_meta() #4."""

        ## test.md: ---\nfoo: True\n... ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"blocks": [], "pandoc-api-version": [%s], "meta": {"foo": {"t": "MetaBool", "c": True}}}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '---\nfoo: True\n...'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(),
            stdin=md.stdout).strip().decode("utf-8").replace('true', 'True'))
        self.assertEqual(src, output)

        expected = True

        # Make the comparison
        self.assertEqual(get_meta(src['meta'], 'foo'), expected)


    def test_insert_secnos_factory_1(self):
        """Tests insert_secnos_factory() #1."""

        ## test.md: ---\nxnos-number-sections: True\n...\n\n# Title\n\n$$ x $$ {#eq:1}\n ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"blocks": [{"t": "Header", "c": [1, ["title", [], []], [{"t": "Str", "c": "Title"}]]}, {"t": "Para", "c": [{"t": "Math", "c": [{"t": "DisplayMath"}, " x "]}, {"t": "Space"}, {"t": "Str", "c": "{#eq:1}"}]}], "pandoc-api-version": [%s], "meta": {"xnos-number-sections": {"t": "MetaBool", "c": True}}}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '---\nxnos-number-sections: True\n...\n\n# Title\n\n$$ x $$ {#eq:1}\n'), stdout=subprocess.PIPE)

        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(),
            stdin=md.stdout).strip().decode("utf-8").replace('true', 'True'))
        self.assertEqual(src, output)

        expected = eval(r'''{"blocks": [{"t": "Header", "c": [1, ["title", [], []], [{"t": "Str", "c": "Title"}]]}, {"t": "Para", "c": [{"t": "Math", "c": [["eq:1", [], [["secno", 1]]], {"t": "DisplayMath"}, " x "]}, {"t": "Space"}]}], "pandoc-api-version": [%s], "meta": {"xnos-number-sections": {"t": "MetaBool", "c": True}}}'''%PANDOC_API_VERSION)

        # Make the comparison
        meta = src['meta']
        fmt = 'html'
        attach_attrs_math = attach_attrs_factory(Math, 0, allow_space=True)
        insert_secnos = insert_secnos_factory(Math)
        tmp = walk(src, attach_attrs_math, fmt, meta)
        self.assertEqual(walk(tmp, insert_secnos, fmt, meta), expected)


    def test_insert_secnos_factory_2(self):
        """Tests insert_secnos_factory() #2."""

        ## test.md: ---\nxnos-number-sections: True\n...\n\n# Title\n\n$$ x $$\n ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"blocks": [{"t": "Header", "c": [1, ["title", [], []], [{"t": "Str", "c": "Title"}]]}, {"t": "Para", "c": [{"t": "Math", "c": [{"t": "DisplayMath"}, " x "]}]}], "pandoc-api-version": [%s], "meta": {"xnos-number-sections": {"t": "MetaBool", "c": True}}}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '---\nxnos-number-sections: True\n...\n\n# Title\n\n$$ x $$\n'), stdout=subprocess.PIPE)

        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(),
            stdin=md.stdout).strip().decode("utf-8").replace('true', 'True'))
        self.assertEqual(src, output)

        expected = eval(r'''{"blocks": [{"t": "Header", "c": [1, ["title", [], []], [{"t": "Str", "c": "Title"}]]}, {"t": "Para", "c": [{"t": "Math", "c": [{"t": "DisplayMath"}, " x "]}]}], "pandoc-api-version": [%s], "meta": {"xnos-number-sections": {"t": "MetaBool", "c": True}}}'''%PANDOC_API_VERSION)

        # Make the comparison
        meta = src['meta']
        fmt = 'html'
        attach_attrs_math = attach_attrs_factory(Math, 0, allow_space=True)
        insert_secnos = insert_secnos_factory(Math)
        tmp = walk(src, attach_attrs_math, fmt, meta)
        self.assertEqual(walk(tmp, insert_secnos, fmt, meta), expected)


    def test_elt(self):
        """Tests elt()."""

        # pylint: disable=no-member
        el = elt('RawBlock', 2)
        self.assertEqual(len(el.__closure__), 2)
        self.assertEqual(el.__closure__[0].cell_contents, 'RawBlock')
        self.assertEqual(el.__closure__[1].cell_contents, 2)


    def test_quotify_1(self):
        """Tests quotify() #1."""

        ## test.md: "test" ##

        # Command: pandoc test.md -f markdown+smart -t json
        src = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Quoted","c":[{"t":"DoubleQuote"},[{"t":"Str","c":"test"}]]}]}],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '"test"'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -f markdown+smart -t json').split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Command: pandoc -f markdown-smart test.md -t json
        expected = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Str","c":"\"test\""}]}],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', '"test"'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -f markdown-smart -t json').split(),
            stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(quotify(src['blocks']), expected['blocks'])


    def test_quotify_2(self):
        """Tests quotify() #2."""

        ## test.md: This is 'test 2'. ##

        # Command: pandoc test.md -f markdown+smart -t json
        src = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Str","c":"This"},{"t":"Space"},{"t":"Str","c":"is"},{"t":"Space"},{"t":"Quoted","c":[{"t":"SingleQuote"},[{"t":"Str","c":"test"},{"t":"Space"},{"t":"Str","c":"2"}]]},{"t":"Str","c":"."}]}],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', "This is 'test 2'."),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -f markdown+smart -t json').split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Command: pandoc -f markdown-smart test.md -t json
        expected = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Str","c":"This"},{"t":"Space"},{"t":"Str","c":"is"},{"t":"Space"},{"t":"Str","c":"'test"},{"t":"Space"},{"t":"Str","c":"2'."}]}],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', "This is 'test 2'."),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -f markdown-smart -t json').split(),
            stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(quotify(src['blocks']), expected['blocks'])


    def test_dollarfy(self):
        """Tests dollarfy()."""

        ## test.md: $\frac{1}{2}$ ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Math","c":[{"t":"InlineMath"},"\\frac{1}{2}"]}]}],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', r'$\frac{1}{2}$'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded
        expected = eval(r'''[{"t": "Str", "c": "$\\frac{1}{2}$"}]''')

        # Make the comparison
        self.assertEqual(dollarfy(src['blocks'][0]['c']), expected)


    def test_extract_attrs_1(self):
        """Tests extract_attrs() #1."""

        ## test.md: Test {#eq:id .class tag="foo"}. ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"blocks":[{"t":"Para","c":[{"t":"Str","c":"Test"},{"t":"Space"},{"t":"Str","c":"{#eq:id"},{"t":"Space"},{"t":"Str","c":".class"},{"t":"Space"},{"t":"Str","c":"tag="},{"t":"Quoted","c":[{"t":"DoubleQuote"},[{"t":"Str","c":"foo"}]]},{"t":"Str","c":"}."}]}],"pandoc-api-version":[%s],"meta":{}}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'Test {#eq:id .class tag="foo"}.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded
        expected = ['eq:id', ['class'], [['tag', 'foo']]]

        # Make the comparison
        self.assertEqual(extract_attrs(src['blocks'][0]['c'], 2).list, expected)


    def test_extract_attrs_2(self):
        """Tests extract_attrs() #2."""

        ## test.md: Test {#eq:id .class tag="foo"}. ##

        # Command: pandoc test.md -f markdown+smart -t json
        src = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Str","c":"Test"},{"t":"Space"},{"t":"Str","c":"{#eq:id"},{"t":"Space"},{"t":"Str","c":".class"},{"t":"Space"},{"t":"Str","c":"tag="},{"t":"Quoted","c":[{"t":"DoubleQuote"},[{"t":"Str","c":"foo"}]]},{"t":"Str","c":"}."}]}],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Check src against pandoc-1.17.2
        md = subprocess.Popen(('echo', 'Test {#eq:id .class tag="foo"}.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -f markdown+smart -t json').split(),\
              stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded
        expected = ['eq:id', ['class'], [['tag', 'foo']]]

        # Make the comparison
        self.assertEqual(extract_attrs(src['blocks'][0]['c'], 2).list, expected)


    # NOTE: Broken refs are fixed with pandoc 1.18
    def test_repair_refs_1(self):
        """Tests repair_refs() #1."""

        ## test.md: {@doe:1999} ##

        # Command: pandoc-1.17.2 test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@doe"}],["mailto:%7B@doe",""]]},{"t":"Str","c":":1999}"}]}]]''')

        # Command: pandoc-1.17.2 test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"doe:1999","citationHash":0}],[{"t":"Str","c":"@doe:1999"}]]},{"t":"Str","c":"}"}]}]]''')

        # Make the comparison
        pandocxnos.init('1.17.2')
        self.assertEqual(walk(src, repair_refs, '', {}), expected)

    # NOTE: Broken refs are fixed with pandoc 1.18
    def test_repair_refs_2(self):
        """Tests repair_refs() #2."""

        ## test.md: Eqs. {@eq:1}a and {@eq:1}b. ##

        # Command: pandoc-1.17.2 test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"Eqs."},{"t":"Space","c":[]},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@eq"}],["mailto:%7B@eq",""]]},{"t":"Str","c":":1}a"},{"t":"Space","c":[]},{"t":"Str","c":"and"},{"t":"Space","c":[]},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@eq"}],["mailto:%7B@eq",""]]},{"t":"Str","c":":1}b."}]}]]''')

        # Command: pandoc-1.17.2 test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"Eqs."},{"t":"Space","c":[]},{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"}a"},{"t":"Space","c":[]},{"t":"Str","c":"and"},{"t":"Space","c":[]},{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"}b."}]}]]''')

        # Make the comparison
        pandocxnos.init('1.17.2')
        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


    # NOTE: Broken refs are fixed with pandoc 1.18
    def test_repair_refs_3(self):
        """Tests repair_refs() #3."""

        ## test.md: See {+@eq:1}. ##

        # Command: pandoc-1.17.2 test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{+@eq"}],["mailto:%7B+@eq",""]]},{"t":"Str","c":":1}."}]}]]''')

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space","c":[]},{"t":"Str","c":"{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"}."}]}]]''')

        # Make the comparison
        pandocxnos.init('1.17.2')
        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


    # NOTE: Broken refs are fixed with pandoc 1.18
    def test_repair_refs_4(self):
        """Tests repair_refs() #4."""

        ## test.md: *@fig:plot1 and {+@fig:plot3}a. ##

        # Command: pandoc-1.17.2 test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"*@fig"}],["mailto:*@fig",""]]},{"t":"Str","c":":plot1"},{"t":"Space","c":[]},{"t":"Str","c":"and"},{"t":"Space","c":[]},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{+@fig"}],["mailto:%7B+@fig",""]]},{"t":"Str","c":":plot3}a."}]}]]''')

        # Command: pandoc-1.17.2 test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"*"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:plot1","citationHash":0}],[{"t":"Str","c":"@fig:plot1"}]]},{"t":"Space","c":[]},{"t":"Str","c":"and"},{"t":"Space","c":[]},{"t":"Str","c":"{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:plot3","citationHash":0}],[{"t":"Str","c":"@fig:plot3"}]]},{"t":"Str","c":"}a."}]}]]''')

        # Make the comparison
        pandocxnos.init('1.17.2')
        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


    # NOTE: Broken refs are fixed with pandoc 1.18
    def test_repair_refs_5(self):
        """Tests repair_refs() #5."""

        ## test.md: +@eq:1, ##

        # Command: pandoc-1.17.2 test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"+@eq"}],["mailto:+@eq",""]]},{"t":"Str","c":":1,"}]}]]''')

        # Command: pandoc-1.17.2 test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":","}]}]]''')

        # Make the comparison
        pandocxnos.init('1.17.2')
        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


    # NOTE: Broken refs are fixed with pandoc 1.18
    def test_repair_refs_6(self):
        """Tests repair_refs() #6."""

        ## test.md: {@fig:1{baz=bat}}a ##

        # Command: pandoc-1.17.2 test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@fig"}],["mailto:%7B@fig",""]]},{"t":"Str","c":":1{baz=bat}}a"}]}]]''')

        # Command: pandoc-1.17.2 test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:1","citationHash":0}],[{"t":"Str","c":"@fig:1"}]]},{"t":"Str","c":"{baz=bat}}a"}]}]]''')

        # Make the comparison
        pandocxnos.init('1.17.2')
        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


    # NOTE: Broken refs are fixed with pandoc 1.18
    def test_repair_refs_7(self):
        """Tests repair_refs() #7."""

        ## test.md: {@fig:1{baz=bat foo=bar}}a ##

        # Command: pandoc-1.17.2 test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@fig"}],["mailto:%7B@fig",""]]},{"t":"Str","c":":1{baz=bat"},{"t":"Space","c":[]},{"t":"Str","c":"foo=bar}}a"}]}]]''')

        # Command: pandoc-1.17.2 test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:1","citationHash":0}],[{"t":"Str","c":"@fig:1"}]]},{"t":"Str","c":"{baz=bat"},{"t":"Space","c":[]},{"t":"Str","c":"foo=bar}}a"}]}]]''')

        # Make the comparison
        pandocxnos.init('1.17.2')
        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


    # NOTE: Broken refs are fixed with pandoc 1.18
    def test_repair_refs_8(self):
        """Tests repair_refs() #8."""

        ## test.md: {@fig:1}-{@fig:3} ##

        # Command: pandoc-1.17.2 test.md -f markdown+autolink_bare_uris -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"{@fig"}],["mailto:%7B@fig",""]]},{"t":"Str","c":":"},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"1}-{@fig"}],["mailto:1%7D-%7B@fig",""]]},{"t":"Str","c":":3}"}]}]]''')

        # Command: pandoc test.md -t json
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:1","citationHash":0}],[{"t":"Str","c":"@fig:1"}]]},{"t":"Str","c":"}-{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:3","citationHash":0}],[{"t":"Str","c":"@fig:3"}]]},{"t":"Str","c":"}"}]}]]''')

        # Make the comparison
        pandocxnos.init('1.17.2')
        self.assertEqual(walk(src, repair_refs, {}, ''), expected)


    def test_process_refs_factory_1(self):
        """Tests process_refs_factory() #1."""

        ## test.md: As shown in @fig:one. ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"blocks":[{"t":"Para","c":[{"t":"Str","c":"As"},{"t":"Space"},{"t":"Str","c":"shown"},{"t":"Space"},{"t":"Str","c":"in"},{"t":"Space"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"fig:one","citationHash":0}],[{"t":"Str","c":"@fig:one"}]]},{"t":"Str","c":"."}]}],"pandoc-api-version":[%s],"meta":{}}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'As shown in @fig:one.'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (added empty attributes)
        expected = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Str","c":"As"},{"t":"Space"},{"t":"Str","c":"shown"},{"t":"Space"},{"t":"Str","c":"in"},{"t":"Space"},{"t":"Cite","c":[["",[],[]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"fig:one","citationHash":0}],[{"t":"Str","c":"@fig:one"}]]},{"t":"Str","c":"."}]}],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Make the comparison
        process_refs = process_refs_factory(None, ['fig:one'], 0)
        self.assertEqual(walk(src, process_refs, '', {}), expected)


    def test_process_refs_factory_2(self):
        """Tests process_refs_factory() #2."""

        ## test.md: (@eq:one) ##

        # Command: pandoc test.md -t json
        src = eval(
            r'''{"blocks":[{"t":"Para","c":[{"t":"Str","c":"("},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"eq:one","citationHash":0}],[{"t":"Str","c":"@eq:one"}]]},{"t":"Str","c":")"}]}],"pandoc-api-version":[%s],"meta":{}}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '(@eq:one)'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(),
            stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (attributes added)
        expected = eval(r'''{"blocks":[{"t":"Para","c":[{"t":"Str","c":"("},{"t":"Cite","c":[["",[],[]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"eq:one","citationHash":0}],[{"t":"Str","c":"@eq:one"}]]},{"t":"Str","c":")"}]}],"pandoc-api-version":[%s],"meta":{}}'''%PANDOC_API_VERSION)

        # Make the comparison
        process_refs = process_refs_factory(None, ['eq:one'], 0)
        self.assertEqual(walk(src, process_refs, '', {}), expected)


    def test_process_refs_factory_3(self):
        """Tests process_refs_factory() #3."""

        ## test.md: See {@tbl:1}. ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"blocks":[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space"},{"t":"Str","c":"{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"tbl:1","citationHash":0}],[{"t":"Str","c":"@tbl:1"}]]},{"t":"Str","c":"}."}]}],"pandoc-api-version":[%s],"meta":{}}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'See {@tbl:1}.'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (braces stripped, attributes added)
        expected = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space"},{"t":"Cite","c":[["",[],[]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"tbl:1","citationHash":0}],[{"t":"Str","c":"@tbl:1"}]]},{"t":"Str","c":"."}]}],"pandoc-api-version":[%s],"meta":{}}'''%PANDOC_API_VERSION)

        # Make the comparison
        process_refs = process_refs_factory(None, ['tbl:1'], 0)
        self.assertEqual(walk(src, process_refs, '', {}), expected)


    def test_process_refs_factory_4(self):
        """Tests process_refs_factory() #4."""

        ## test.md: See +@eq:1. ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"blocks":[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space"},{"t":"Str","c":"+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"."}]}],"pandoc-api-version":[%s],"meta":{}}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'See +@eq:1.'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (modifier extracted, attributes added)
        expected = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space"},{"t":"Cite","c":[["",[],[["modifier","+"]]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"@eq:1"}]]},{"t":"Str","c":"."}]}],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Make the comparison
        process_refs = process_refs_factory(None, ['eq:1'], 0)
        self.assertEqual(walk(src, process_refs, '', {}), expected)


    def test_process_refs_factory_5(self):
        """Tests process_refs_factory() #5."""

        ## test.md: See {+@tbl:1}. ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"blocks":[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space"},{"t":"Str","c":"{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"tbl:1","citationHash":0}],[{"t":"Str","c":"@tbl:1"}]]},{"t":"Str","c":"}."}]}],"pandoc-api-version":[%s],"meta":{}}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'See {+@tbl:1}.'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (braces stripped, modifier extracted, attributes added)
        expected = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space"},{"t":"Cite","c":[["",[],[["modifier","+"]]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"tbl:1","citationHash":0}],[{"t":"Str","c":"@tbl:1"}]]},{"t":"Str","c":"."}]}],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Make the comparison
        process_refs = process_refs_factory(None, ['tbl:1'], 0)
        self.assertEqual(walk(src, process_refs, '', {}), expected)


    def test_process_refs_factory_6(self):
        """Tests process_refs_factory() #6."""

        ## test.md: See xxx{+@tbl:1}xxx. ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"blocks":[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space"},{"t":"Str","c":"xxx{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"tbl:1","citationHash":0}],[{"t":"Str","c":"@tbl:1"}]]},{"t":"Str","c":"}xxx."}]}],"pandoc-api-version":[%s],"meta":{}}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'See xxx{+@tbl:1}xxx.'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (braces stripped, modifier extracted, attributes added)
        expected = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space"},{"t":"Str","c":"xxx"},{"t":"Cite","c":[["",[],[["modifier","+"]]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"tbl:1","citationHash":0}],[{"t":"Str","c":"@tbl:1"}]]},{"t":"Str","c":"xxx."}]}],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Make the comparison
        process_refs = process_refs_factory(None, ['tbl:1'], 0)
        self.assertEqual(walk(src, process_refs, '', {}), expected)


    def test_process_refs_factory_7(self):
        """Tests process_refs_factory() #7."""

        ## test.md: See [+@eq:1]. ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"blocks":[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"NormalCitation"},"citationPrefix":[{"t":"Str","c":"+"}],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"[+@eq:1]"}]]},{"t":"Str","c":"."}]}],"pandoc-api-version":[%s],"meta":{}}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', 'See [+@eq:1].'), stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (modifier extracted, attributes added)
        expected = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Str","c":"See"},{"t":"Space"},{"t":"Cite","c":[["",[],[["modifier","+"]]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"NormalCitation"},"citationPrefix":[],"citationId":"eq:1","citationHash":0}],[{"t":"Str","c":"[+@eq:1]"}]]},{"t":"Str","c":"."}]}],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Make the comparison
        process_refs = process_refs_factory(None, ['eq:1'], 0)
        self.assertEqual(walk(src, process_refs, '', {}), expected)


    def test_use_refs_factory_7(self):
        """Tests use_refs_factory() #7."""

        ## test.md: {+@tbl:one}-{@tbl:four} provide the data. ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"blocks":[{"t":"Para","c":[{"t":"Str","c":"{+"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"tbl:one","citationHash":0}],[{"t":"Str","c":"@tbl:one"}]]},{"t":"Str","c":"}-{"},{"t":"Cite","c":[[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"tbl:four","citationHash":0}],[{"t":"Str","c":"@tbl:four"}]]},{"t":"Str","c":"}"},{"t":"Space"},{"t":"Str","c":"provide"},{"t":"Space"},{"t":"Str","c":"the"},{"t":"Space"},{"t":"Str","c":"data."}]}],"pandoc-api-version":[%s],"meta":{}}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(
            ('echo', '{+@tbl:one}-{@tbl:four} provide the data.'),
            stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded
        expected = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Cite","c":[["",[],[["modifier","+"]]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"tbl:one","citationHash":0}],[{"t":"Str","c":"@tbl:one"}]]},{"t":"Str","c":"-"},{"t":"Cite","c":[["",[],[]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText"},"citationPrefix":[],"citationId":"tbl:four","citationHash":0}],[{"t":"Str","c":"@tbl:four"}]]},{"t":"Space"},{"t":"Str","c":"provide"},{"t":"Space"},{"t":"Str","c":"the"},{"t":"Space"},{"t":"Str","c":"data."}]}],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Make the comparison
        process_refs = process_refs_factory(None, ['tbl:one', 'tbl:four'], 0)
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
            (PANDOC1p15 + ' -t json').split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Generate expected using current pandoc
        md = subprocess.Popen(('echo', '@fig:1:'), stdout=subprocess.PIPE)
        expected = eval(subprocess.check_output(
            (PANDOC+' -t json').split(), stdin=md.stdout).strip())

        # Make the comparison
        process_refs = process_refs_factory(None, ['fig:1'], 0)
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
            (PANDOC1p15 + ' -t json').split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Cite","c":[["",[],[]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:1","citationHash":0}],[{"t":"Str","c":"@fig:1"}]]},{"t":"Str","c":":"}]}]]''')

        # Make the comparison
        process_refs = process_refs_factory(None, ['fig:1'], 0)
        self.assertEqual(walk(src, process_refs, {}, ''), expected)


    def test_replace_refs_factory(self):
        """Tests replace_refs_factory."""

        ## test.md: As shown in @fig:1. ##

        # Command: pandoc-1.15.2 test.md -t json
        src = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"As"},{"t":"Space","c":[]},{"t":"Str","c":"shown"},{"t":"Space","c":[]},{"t":"Str","c":"in"},{"t":"Space","c":[]},{"t":"Cite","c":[["",[],[]],[{"citationSuffix":[],"citationNoteNum":0,"citationMode":{"t":"AuthorInText","c":[]},"citationPrefix":[],"citationId":"fig:one","citationHash":0}],[{"t":"Str","c":"@fig:one"}]]},{"t":"Str","c":"."}]}]]''')

        # Hand-coded
        expected = eval(r'''[{"unMeta":{}},[{"t":"Para","c":[{"t":"Str","c":"As"},{"t":"Space","c":[]},{"t":"Str","c":"shown"},{"t":"Space","c":[]},{"t":"Str","c":"in"},{"t":"Space","c":[]},{"t":"Str","c":"fig.\u00A0"},{'t':'Link','c':[['',[],[]],[{'t':'Str','c':'1'}],['#fig:one','']]},{"t":"Str","c":"."}]}]]''')

        # Make the comparison
        replace_refs = replace_refs_factory({'fig:one':pandocxnos.Target(1, 1)},
                                            True, False,
                                            ['fig.', 'figs.'],
                                            ['Figure', 'Figures'])
        self.assertEqual(walk(walk(src, replace_refs, {}, ''),
                              join_strings, {}, ''), expected)


    def test_attach_attrs_factory(self):
        """Tests attach_attrs_math()."""

        attach_attrs_math = attach_attrs_factory(Math, 0, allow_space=True)

        ## test.md: $$ y = f(x) $${#eq:1 tag="B.1"} ##

        # Command: pandoc test.md -t json
        src = eval(r'''{"blocks":[{"t":"Para","c":[{"t":"Math","c":[{"t":"DisplayMath"}," y = f(x) "]},{"t":"Str","c":"{#eq:1"},{"t":"Space"},{"t":"Str","c":"tag="},{"t":"Quoted","c":[{"t":"DoubleQuote"},[{"t":"Str","c":"B.1"}]]},{"t":"Str","c":"}"}]}],"pandoc-api-version":[%s],"meta":{}}'''%PANDOC_API_VERSION)

        # Check src against current pandoc
        md = subprocess.Popen(('echo', '$$ y = f(x) $${#eq:1 tag="B.1"}'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(), stdin=md.stdout).strip())
        self.assertEqual(src, output)

        # Hand-coded (attributes deleted)
        expected = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Math","c":[["eq:1",[],[["tag","B.1"]]],{"t":"DisplayMath"}," y = f(x) "]}]}],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # Make the comparison
        self.assertEqual(walk(src, attach_attrs_math, '', {}), expected)


    def test_detach_attrs_factory(self):
        """Tests filter_attrs_factory()."""

        detach_attrs_math = detach_attrs_factory(Math)

        ## Use 'expected' from test_attach_attrs_factory ##

        src = eval(r'''{"meta":{},"blocks":[{"t":"Para","c":[{"t":"Math","c":[["eq:1",[],[["tag","B.1"]]],{"t":"DisplayMath"}," y = f(x) "]}]}],"pandoc-api-version":[%s]}'''%PANDOC_API_VERSION)

        # test.md: $$ y = f(x) $$
        # Command: pandoc test.md -t json
        expected = eval(r'''{"blocks":[{"t":"Para","c":[{"t":"Math","c":[{"t":"DisplayMath"}," y = f(x) "]}]}],"pandoc-api-version":[%s],"meta":{}}'''%PANDOC_API_VERSION)

        # Check expected against current pandoc
        md = subprocess.Popen(('echo', '$$ y = f(x) $$'),
                              stdout=subprocess.PIPE)
        output = eval(subprocess.check_output(
            (PANDOC+' -t json').split(), stdin=md.stdout).strip())
        self.assertEqual(expected, output)

        # Make the comparison
        self.assertEqual(walk(src, detach_attrs_math, '', {}), expected)


# pylint: disable=too-few-public-methods
class TestPandocAttributes(unittest.TestCase):
    """Test the pandocattributes package."""

    def test_kvs(self):
        """Tests PandocAttributes.kvs."""
        attrs = PandocAttributes(['', [], [['tag', 'B.1']]], 'pandoc')
        kvs = attrs.kvs

        # Ensure that changing the kvs changes attrs too
        kvs['tag'] = 'B.3'
        self.assertEqual(attrs['tag'], 'B.3')


#-----------------------------------------------------------------------------
# main()

def main():
    """Runs the suite of unit tests"""

    # Do the tests
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(TestXnos))
    suite.addTests(unittest.makeSuite(TestPandocAttributes))
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

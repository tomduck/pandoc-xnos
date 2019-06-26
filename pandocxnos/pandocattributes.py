# Copyright 2014-2015 Aaron O'Leary <dev@aaren.me>
# Copyright 2019 Thomas J. Duck <tomduck@tomduck.ca>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""pandocattributes.py - pandoc block attributes management.

Usage:

    attrs = '#id .class1 .class2 key=value'
    attributes = PandocAttributes(attrs, 'markdown')

    attributes.to_pandoc()
    >>> ['id', ['class1', 'class2'], [['key', 'value']]]

    attributes.to_markdown()
    >>> '{#id .class1 .class2 key=value}'

    attributes.to_html()
    >>> id="id" class="class1 class2" key='value'

    attributes.id
    >>> 'id'

    attributes.classes
    >>> ['class1', 'class2']

    attributes.kvs
    >>> OrderedDict([('key', 'value')])
"""


import re
from collections import OrderedDict

# pylint: disable=useless-object-inheritance
class PandocAttributes(object):
    """Parser / Emitter for pandoc block attributes."""

    spnl = ' \n'
    split_regex = r'''((?:[^{separator}"']|"[^"]*"|'[^']*')+)'''.format

    parse_failed = False  # Flags if not all fields were parsed
    attrstr = None        # The original attribute string

    def __init__(self, attrstr=None, fmt='pandoc'):
        """Initializes the attributes."""
        if attrstr is None:
            id_ = ''
            classes = []
            kvs = OrderedDict()
        elif fmt == 'pandoc':
            id_, classes, kvs = self._parse_pandoc(attrstr)
        elif fmt == 'markdown':
            id_, classes, kvs = self._parse_markdown(attrstr)
        else:
            raise UserWarning('invalid format')

        self.id = id_
        self.classes = classes
        self.kvs = kvs
        self.attrstr = attrstr

    @staticmethod
    def _parse_pandoc(attrs):
        """Read pandoc attributes."""
        id_ = attrs[0]
        classes = attrs[1]
        kvs = OrderedDict(attrs[2])
        return id_, classes, kvs

    def _parse_markdown(self, attrstr):
        """Read markdown attributes."""
        attrstr = attrstr.strip('{}')
        splitter = re.compile(self.split_regex(separator=self.spnl))
        attrs = splitter.split(attrstr)[1::2]

        # Match single word attributes e.g. python
        if len(attrs) == 1 \
                and not attrstr.startswith(('#', '.')) \
                and '=' not in attrstr:
            return '', [attrstr], OrderedDict()

        try:
            id_ = [a[1:] for a in attrs if a.startswith('#')][0]
        except IndexError:
            id_ = ''

        classes = [a[1:] for a in attrs if a.startswith('.')]
        special = ['unnumbered' for a in attrs if a == '-']
        classes.extend(special)

        nkvs = sum(1 for a in attrs if not a.startswith(('#', '.'))
                   and a != '-')
        kvs = OrderedDict(a.split('=', 1) for a in attrs
                          if '=' in a and a[0] != '=' and a[-1] != '=')

        if len(kvs) != nkvs:
            self.parse_failed = True

        return id_, classes, kvs

    def to_pandoc(self):
        """Returns the attributes as a pandoc-compatibile list."""
        kvs = [[k, v] for k, v in self.kvs.items()]
        return [self.id, self.classes, kvs]

    def to_markdown(self, fmt='{id} {classes} {kvs}', surround=True):
        """Returns attributes formatted as markdown with optional
        fmt argument to determine order of attribute contents.
        """
        id_ = '#' + self.id if self.id else ''
        classes = ' '.join('.' + cls for cls in self.classes)
        kvs = ' '.join('{}={}'.format(k, v) for k, v in self.kvs.items())

        attrs = fmt.format(id=id_, classes=classes, kvs=kvs).strip()

        if surround:
            return '{' + attrs + '}'
        return attrs

    def to_html(self):
        """Returns attributes formatted as html."""
        id_, classes, kvs = self.id, self.classes, self.kvs
        id_str = 'id="{}"'.format(id_) if id_ else ''
        class_str = 'class="{}"'.format(' '.join(classes)) if classes else ''
        key_str = ' '.join('{}={}'.format(k, v) for k, v in kvs.items())
        return ' '.join((id_str, class_str, key_str)).strip()

    @property
    def list(self):
        """The attributes in list form."""
        return self.to_pandoc()

    @property
    def markdown(self):
        """The attributes in html form."""
        return self.to_markdown()

    @property
    def html(self):
        """The attributes in html form."""
        return self.to_html()

    @property
    def is_empty(self):
        """Returns True if the attributes are empty; False otherwise."""
        return self.id == '' and self.classes == [] and self.kvs == {}

    def __getitem__(self, item):
        """Gets 'id', 'classes', or an attribute."""
        if item == 'id':
            return self.id
        if item == 'classes':
            return self.classes
        return self.kvs[item]

    def __setitem__(self, key, value):
        """Sets 'id', 'classes', or an attribute."""
        if key == 'id':
            self.id = value
        elif key == 'classes':
            self.classes = value
        else:
            self.kvs[key] = value

    def __contains__(self, key):
        """Returns True if key is 'id', 'classes', or an attribute;
        False otherwise."""
        return key == 'id' or key == 'classes' or key in self.kvs

    def __iter__(self):
        """Returns an interator over the kvs."""
        return iter(self.kvs)

    def items(self):
        """Returns the kv items."""
        return self.kvs.items()

    def __repr__(self):
        """Returns the string representation of self."""
        return "pandocfilters.Attributes({})".format(self.to_pandoc())

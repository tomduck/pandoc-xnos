
# Copyright 2014-2015 Aaron O'Leary <dev@aaren.me>
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

import re
from collections import OrderedDict


class PandocAttributes(object):
    """Parser / Emitter for pandoc block attributes.

    Can read and write attributes in any of these formats:
        - markdown
        - html
        - dictionary
        - pandoc

    usage:
        attrs = '#id .class1 .class2 key=value'
        attributes = PandocAttributes(attrs, format='markdown')

        attributes.to_markdown()
        >>> '{#id .class1 .class2 key=value}'

        attributes.to_dict()
        >>> {'id': 'id', 'classes': ['class1', 'class2'], 'key'='value'}

        attributes.to_html()
        >>> id="id" class="class1 class2" key='value'

        attributes.to_pandoc()
        >>> ['id', ['class1', 'class2'], [['key', 'value']]]

        attributes.id
        >>> 'id'

        attributes.classes
        >>> ['class1', 'class2']

        attributes.kvs
        >>> OrderedDict([('key', 'value')])
    """
    spnl = ' \n'
    split_regex = r'''((?:[^{separator}"']|"[^"]*"|'[^']*')+)'''.format

    def __init__(self, attr=None, format='pandoc'):
        if attr is None:
            id = ''
            classes = []
            kvs = OrderedDict()
        elif format == 'pandoc':
            id, classes, kvs = self.parse_pandoc(attr)
        elif format == 'markdown':
            id, classes, kvs = self.parse_markdown(attr)
        elif format == 'html':
            id, classes, kvs = self.parse_html(attr)
        elif format == 'dict':
            id, classes, kvs = self.parse_dict(attr)
        else:
            raise UserWarning('invalid format')

        self.id = id
        self.classes = classes
        self.kvs = kvs

    @classmethod
    def parse_pandoc(self, attrs):
        """Read pandoc attributes."""
        id = attrs[0]
        classes = attrs[1]
        kvs = OrderedDict(attrs[2])

        return id, classes, kvs

    @classmethod
    def parse_markdown(self, attr_string):
        """Read markdown attributes."""
        attr_string = attr_string.strip('{}')
        splitter = re.compile(self.split_regex(separator=self.spnl))
        attrs = splitter.split(attr_string)[1::2]

        # match single word attributes e.g. ```python
        if len(attrs) == 1 \
                and not attr_string.startswith(('#', '.')) \
                and '=' not in attr_string:
            return '', [attr_string], OrderedDict()

        try:
            id = [a[1:] for a in attrs if a.startswith('#')][0]
        except IndexError:
            id = ''

        classes = [a[1:] for a in attrs if a.startswith('.')]
        special = ['unnumbered' for a in attrs if a == '-']
        classes.extend(special)

        kvs = OrderedDict(a.split('=', 1) for a in attrs if '=' in a)

        return id, classes, kvs

    def parse_html(self, attr_string):
        """Read a html string to attributes."""
        splitter = re.compile(self.split_regex(separator=self.spnl))
        attrs = splitter.split(attr_string)[1::2]

        idre = re.compile(r'''id=["']?([\w ]*)['"]?''')
        clsre = re.compile(r'''class=["']?([\w ]*)['"]?''')

        id_matches = [idre.search(a) for a in attrs]
        cls_matches = [clsre.search(a) for a in attrs]

        try:
            id = [m.groups()[0] for m in id_matches if m][0]
        except IndexError:
            id = ''

        classes = [m.groups()[0] for m in cls_matches if m][0].split()

        special = ['unnumbered' for a in attrs if '-' in a]
        classes.extend(special)

        kvs = [a.split('=', 1) for a in attrs if '=' in a]
        kvs = OrderedDict((k, v) for k, v in kvs if k not in ('id', 'class'))

        return id, classes, kvs

    @classmethod
    def parse_dict(self, attrs):
        """Read a dict to attributes."""
        attrs = attrs or {}
        ident = attrs.get("id", "")
        classes = attrs.get("classes", [])
        kvs = OrderedDict((k, v) for k, v in attrs.items()
                          if k not in ("classes", "id"))

        return ident, classes, kvs

    def to_markdown(self, format='{id} {classes} {kvs}', surround=True):
        """Returns attributes formatted as markdown with optional
        format argument to determine order of attribute contents.
        """
        id = '#' + self.id if self.id else ''
        classes = ' '.join('.' + cls for cls in self.classes)
        kvs = ' '.join('{}={}'.format(k, v) for k, v in self.kvs.items())

        attrs = format.format(id=id, classes=classes, kvs=kvs).strip()

        if surround:
            return '{' + attrs + '}'
        elif not surround:
            return attrs

    def to_html(self):
        """Returns attributes formatted as html."""
        id, classes, kvs = self.id, self.classes, self.kvs
        id_str = 'id="{}"'.format(id) if id else ''
        class_str = 'class="{}"'.format(' '.join(classes)) if classes else ''
        key_str = ' '.join('{}={}'.format(k, v) for k, v in kvs.items())
        return ' '.join((id_str, class_str, key_str)).strip()

    def to_dict(self):
        """Returns attributes formatted as a dictionary."""
        d = {'id': self.id, 'classes': self.classes}
        d.update(self.kvs)
        return d

    def to_pandoc(self):
        kvs = [[k, v] for k, v in self.kvs.items()]
        return [self.id, self.classes, kvs]

    @property
    def markdown(self):
        return self.to_markdown()

    @property
    def html(self):
        return self.to_html()

    @property
    def dict(self):
        return self.to_dict()

    @property
    def list(self):
        return self.to_pandoc()

    @property
    def is_empty(self):
        return self.id == '' and self.classes == [] and self.kvs == {}

    def __getitem__(self, item):
        if item == 'id':
            return self.id
        elif item == 'classes':
            return self.classes
        else:
            return self.kvs[item]

    def __setitem__(self, key, value):
        if key == 'id':
            self.id = value
        elif key == 'classes':
            self.classes = value
        else:
            self.kvs[key] = value

    def __repr__(self):
        return "pandocfilters.Attributes({})".format(self.to_pandoc())

#! /usr/bin/env python3

"""main: a wrapper for the pandoc-fignos/eqnos/tablenos/secnos filters."""

# Copyright 2015-2020 Thomas J. Duck.
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

import io

from pandocxnos import STDIN, STDOUT

FILTERS = ['pandoc_fignos', 'pandoc_eqnos', 'pandoc_tablenos', 'pandoc_secnos']

def main():
    """Main program."""

    stdin = STDIN
    for name in FILTERS:
        try:
            stdout = io.TextIOWrapper(io.BytesIO(), STDOUT.encoding)
            m = __import__(name)
            if m.__version__ < '2.0.0':
                msg = '%s must have version number 2.0.0 or higher to be'\
                      'called by the pandoc-xnos filter.' % name
                raise RuntimeError(msg)
            m.main(stdin, stdout)
            stdin = stdout
            stdin.seek(0)
        except ImportError:
            pass
    STDOUT.write(stdin.read())
    STDOUT.flush()

if __name__ == '__main__':
    main()

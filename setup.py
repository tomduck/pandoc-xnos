"""setup.py - install script for pandoc-xnos."""

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

import re
import io

from setuptools import setup

# pylint: disable=invalid-name

DESCRIPTION = 'Library code for the pandoc-xnos filter suite.'

# From https://stackoverflow.com/a/39671214
__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
    io.open('pandocxnos/core.py', encoding='utf_8_sig').read()
    ).group(1)

setup(
    name='pandoc-xnos',
    version=__version__,

    author='Thomas J. Duck',
    author_email='tomduck@tomduck.ca',
    description=DESCRIPTION,
    long_description=DESCRIPTION,
    license='GPL',
    keywords='pandoc filters',
    url='https://github.com/tomduck/pandoc-xnos',
    download_url='https://github.com/tomduck/pandoc-xnos/tarball/'+__version__,

    install_requires=['pandocfilters>=1.4.2,<2',
                      'psutil>=4.1.0,<6'],

    packages=['pandocxnos'],
    entry_points={'console_scripts':['pandoc-xnos = pandocxnos:main']},

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python'
        ],
)

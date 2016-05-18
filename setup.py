"""setup.py - install script for pandoc-xnos."""

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

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

DESCRIPTION = 'Library code for the pandoc-fignos/eqnos/tablenos filters.'

VERSION = '0.3'

setup(
    name='pandoc-xnos',
    version=VERSION,

    author='Thomas J. Duck',
    author_email='tomduck@tomduck.ca',
    description=DESCRIPTION,
    long_description=DESCRIPTION,
    license='GPL',
    keywords='pandoc filters',
    url='https://github.com/tomduck/pandoc-xnos',
    download_url='https://github.com/tomduck/pandoc-xnos/tarball/'+VERSION,

    install_requires=['pandocfilters>=1.3.0',
                      'pandoc-attributes>=0.1.7',
                      'psutil>=4.1.0'],

    packages=['pandocxnos'],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python'
        ],
)

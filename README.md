
pandoc-xnos
===========

The *pandoc-xnos* filter suite provides facilities for cross-referencing in markdown documents processed by [pandoc]. Individual filters are maintained in separate projects.  They are:

* [pandoc-fignos]: Numbers figures and figure references.
* [pandoc-eqnos]: Numbers equations and equation references.
* [pandoc-tablenos]: Numbers tables and table references.
* [pandoc-secnos]: Numbers section references (sections are
  numbered by pandoc itself).

Click on the above links to access documentation for each filter.   LaTeX/pdf, html, and epub output have native support.  Native support for docx output is a work in progress.

This project provides library code for the suite and a `pandoc-xnos` filter that applies all of the above filters in sequence.

See also: [pandoc-comments], [pandoc-latex-extensions]

[pandoc]: http://pandoc.org/
[pandoc-fignos]: https://github.com/tomduck/pandoc-fignos
[pandoc-eqnos]: https://github.com/tomduck/pandoc-eqnos
[pandoc-tablenos]: https://github.com/tomduck/pandoc-tablenos
[pandoc-secnos]: https://github.com/tomduck/pandoc-secnos
[pandoc-comments]: https://github.com/tomduck/pandoc-comments
[pandoc-latex-extensions]: https://github.com/tomduck/pandoc-latex-extensions


Contents
--------

 1. [Installation](#installation)
 2. [Usage](#usage)
 3. [Getting Help](#getting-help)


Installation
------------

Pandoc-xnos requires [python], a programming language that comes pre-installed on macOS and linux.  It is easily installed on Windows -- see [here](https://realpython.com/installing-python/).  Either python 2.7 or 3.x will do.

The pandoc-xnos filter suite may be installed using the shell command

    pip install pandoc-fignos pandoc-eqnos pandoc-tablenos \
                pandoc-secnos --user

and upgraded by appending `--upgrade` to the above command.

Pip is a program that downloads and installs software from the Python Package Index, [PyPI].  It normally comes installed with a python distribution.<sup>[2](#footnote2)</sup>

Instructions for installing from source are given in [DEVELOPERS.md].

[python]: https://www.python.org/
[PyPI]: https://pypi.python.org/pypi
[DEVELOPERS.md]: DEVELOPERS.md


Usage
-----

The pandoc-xnos filter suite may be applied using the

    --filter pandoc-xnos

option with pandoc.  It is also possible to apply the filters individually.

Any use of `--filter pandoc-citeproc` or `--bibliography=FILE` should come *after* the `pandoc-xnos` filter call.


Getting Help
------------

If you have any difficulties with pandoc-xnos, or would like to see a new feature, then please submit a report to our [Issues tracker].

[Issues tracker]: https://github.com/tomduck/pandoc-xnos/issues

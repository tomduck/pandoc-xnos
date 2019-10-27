
Developer Notes
===============

Branches
--------

The next release is developed in the `nextrelease` branch.  When ready, the changes are merged into the `master` branch.

A copy of the 1.x release series is maintained in the 1.x branch.


Install Alternatives
--------------------

There are a few different options for installing from source:
    
1) To install from the github `master` branch use:

       pip install git+https://github.com/tomduck/pandoc-xnos.git --user

   (to upgrade append the `--upgrade` flag).

2) To install from the `nextrelease` branch on github, use

       pip install git+https://github.com/tomduck/pandoc-xnos.git@nextrelease --user

   (to upgrade use the --upgrade flag).

3) To install from a local source distribution, `cd` into its root
   and use

       pip install -e . --user

   Note that any changes made to the source will be automatically
   reflected when a filter is run (which is useful for development).


Testing
-------

Unit tests for pandoc-xnos are provided in `test/`.  Integration tests are in `test/integration`.


Preparing a Release
-------------------

### Merging ####

Merge the `nextrelease` branch into `master` using

    git checkout master
    git merge nextrelease
    git push


### Tagging ###

See https://www.python.org/dev/peps/pep-0440/ for numbering conventions, including for pre-releases.
    
Tagging  (update the version number):

    git tag -a 2.2.0 -m "New release."
    git push origin 2.2.0


### Distributing ###

Creating source and binary distributions:

    python3 setup.py sdist bdist_wheel

(see https://packaging.python.org/tutorials/packaging-projects/).
    
Uploading to pypi (update the version number):

    twine upload dist/pandoc-xnos-2.2.0.tar.gz \
                   dist/pandoc_xnos-2.2.0-py3-none-any.whl

(see https://pypi.python.org/pypi/twine).

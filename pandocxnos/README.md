
The pandocxnos library
======================

The *pandocxnos* library supports the pandoc-[fignos]/[eqnos]/[tablenos]/[secnos] filters.  Below is a short summary of what is available.  More details are given in module and function docstrings.

[fignos]: https://github.com/tomduck/pandoc-fignos
[eqnos]: https://github.com/tomduck/pandoc-eqnos
[tablenos]: https://github.com/tomduck/pandoc-tablenos
[secnos]: https://github.com/tomduck/pandoc-tablenos
[pandoc]: http://pandoc.org/


core.py
-------

### Globals ###

  * `STRTYPES` - a list of string types for this python version
  * `STDIN`/`STDOUT`/`STDERR` - streams for use with pandoc 2.x or 3.x

### Utility functions ###

  * `init()` - Determines and returns the pandoc version
  * `check_bool()` - Used to check if a variable is boolean
  * `get_meta()` - Retrieves variables from a document's metadata
  * `elt()` - Used to create pandoc AST elements
  * `add_to_header_includes()` - Adds header-includes to metadata
  * `cleveref_required()` - Returns True if cleveref usage was found

### Element list functions ###

  * `quotify()` - Changes Quoted elements to quoted strings
  * `dollarfy()` - Changes Math elements to dollared strings
  * `extract_attrs()` - Extracts attribute strings

### Actions and their factory functions ###

  * `join_strings()` - Joins adjacent strings in a pandoc document
  * `repair_refs()` - Repairs broken Cite elements for pandoc < 1.18
  * `process_refs_factory()` - Makes functions that process
                               references
  * `replace_refs_factory()` - Makes functions that replace refs with
                               format-specific content
  * `attach_attrs_factory()` - Makes functions that attach attributes
                               to elements
  * `detach_attrs_factory()` - Makes functions that detach attributes
                               from elements
  * `insert_secnos_factory()` - Makes functions that insert section
                                numbers into attributes
  * `delete_secnos_factory()` - Makes functions that delete section
                                numbers from attributes
  * `insert_rawblocks_factory()` - Makes function to insert
                                   non-duplicate RawBlock elements.


pandocattributes.py
-------------------

This is a modified version of Aaron O'Leary's project of the same name (https://github.com/aaren/pandoc-attributes).  It provides facilities for managing attributes in pandoc.


main.py
-------

This is a pandoc filter that calls pandoc-fignos/eqnos/tablenos/secnos in sequence (if available).

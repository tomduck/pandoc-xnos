

NOTE: This is a work in progress and not yet an official release.


pandocfiltering 0.1
===================

*pandocfiltering* provides facilities to support the writing of pandoc filters.  It should be used in tandem with the [pandocfilters] module.

This package provides a foundation for the pandoc-[fignos]/[eqnos]/[tablenos] filters.

I am pleased to receive bug reports and feature requests on the project's [Issues tracker].

[pandocfilters]: https://github.com/jgm/pandocfilters
[fignos]: https://github.com/tomduck/pandoc-fignos
[eqnos]: https://github.com/tomduck/pandoc-eqnos
[tablenos]: https://github.com/tomduck/pandoc-tablenos
[Issues tracker]: https://github.com/tomduck/pandocfiltering/issues


Initialization
--------------

##### init(pandocversion=None) #####

Initializes the module.  You may call this at any time to manually set the pandoc version string.  Otherwise the function will determine pandoc's version using subprocess calls.

Note that pandoc [does not provide] version information in its json syntax tree.

[does not provide]: https://github.com/jgm/pandoc/issues/2640


Constants
---------

##### PANDOCVERSION  #####

A string that provides the pandoc version (e.g., "1.17.0.2").


##### STRTYPES #####

Python 2 and 3 have different string types.  This constant lists what is available.


Streams
-------

##### STDIN/STDOUT/STDERR #####

Pandoc uses UTF-8 for both input and output; so must its filters.  Python's `sys.stdin`/`stdout`/`stderr` behaviours differ between versions 3 and 4.  Use these instead.


Functions
---------

##### get_meta(meta, name) #####

Retrieves the metadata variable `name` from the dict `meta`.


##### extract_attrs(value, n) #####

Extracts attributes from a `value` list beginning at index `n`.

The attributes string is removed from the `value` list.  Value items before index `n` are left unchanged.
    
Returns the attributes in pandoc format.  A `ValueError` is raised if attributes aren't found.  An `IndexError` is raised if the index `n` is out of range.


##### quotify(x) #####

Replaces `Quoted` elements with quoted strings.

Pandoc uses the `Quoted` element in its json when `--smart` is enabled.  Output to TeX/pdf automatically triggers `--smart`.

`stringify()` ignores `Quoted` elements.  Use `quotify()` first to replace `Quoted` elements in `x` with quoted strings.  You should provide a deep copy of `x` so that the document is left untouched.

Returns `x`.


##### dollarfy(x) #####

Replaces Math elements with a $-enclosed string.

`stringify()` passes through TeX math.  Use `dollarfy(x)` first to replace `Math` elements with math strings set in dollars.  You should provide a deep copy of `x` so that the document is left untouched.

Returns `x`.


Actions and Their Factory Functions
-----------------------------------

### References ###

##### repair_refs(key, value, fmt, meta) #####

Using `-f markdown+autolink_bare_uris` splits braced references like `{+@label:id}` at the `:` into `Link` and `Str` elements.  This function replaces the mess with the `Cite` and `Str` elements normally found.  Call this action before any reference processing.


##### use_refs_factory(references) #####

Returns `use_refs(key, value, fmt, meta)` action that replaces listed `references` (e.g., `['fig:1', 'fig:2', ...]`) with `Ref` elements.  `Ref` elements aren't understood by pandoc, but are easily identified for further processing by other actions (such as those produced by `replace_refs_factory()`).


##### replace_refs_factory(references, cleveref_default, plusname, starname) #####

Returns `replace_refs(key, value, fmt, meta)` action that replaces
`Ref` elements with text provided by the `references` dict (e.g., `{ 'fig:1':1, 'fig:2':2, ...}`).  Clever referencing is used if `cleveref_default` is `True`, or if "modifier" in the `Ref`'s attributes is "+" or "*".  The `target` is the LaTeX type for clever referencing (`figure`, `equation`, `table`, ...).  The `plusname` and `starname` lists give the singular and plural names for "+" and "*" clever references, respectively.


##### joinstrings(key, value, fmt, meta) #####

Joins adjacent `Str` elements.  Use this as the last action to get json like pandoc would normally produce.  This isn't technically necessary, but is helpful for unit testing.


### Attributes ###

Pandoc only supports attributes for a select few elements.  The following actions allow attributes to be attached, and later filtered, for any element.


##### use_attrs_factory(name, extract_attrs=extract_attrs, allow_space=False) #####

Returns `use_attrs(key, value, fmt, meta)` action that attaches attributes to elements of given name (e.g., `'Image'`, `'Math'`, ...) found in `Para` and `Plain` blocks.

The `extract_attrs()` function should read the attributes and raise a `ValueError` or `IndexError` if attributes are not found.


##### filter_attrs_factory(name, n) #####

Returns `filter_attrs(key, value, fmt, meta)` action that replaces  elements of a given name (e.g., `'Image'`, `'Math'`, ...) with unattributed versions of standard length `n`.



NOTE: This is a work in progress and not yet an official release.


pandocfiltering 0.1
===================

*pandocfiltering* provides facilities to support the writing of pandoc filters.  It should be used in tandem with the [pandocfilters] module.

I am pleased to receive bug reports and feature requests on the project's [Issues tracker].

[pandocfilters]: https://github.com/jgm/pandocfilters
[fignos]: https://github.com/tomduck/pandoc-fignos
[eqnos]: https://github.com/tomduck/pandoc-eqnos
[tablenos]: https://github.com/tomduck/pandoc-tablenos
[Issues tracker]: https://github.com/tomduck/pandocfiltering/issues


Initialization
--------------

##### `init(pandocversion=None)` #####

Initializes the module.  You may call this at any time to manually set the pandoc version.  Otherwise the module will try to determine pandoc's version for itself.


Constants
---------

##### `PANDOCVERSION`  #####

Pandoc [does not provide] version information in its json syntax tree.  This is needed by filters to provide support for multiple pandoc versions.

[does not provide]: https://github.com/jgm/pandoc/issues/2640


Streams
-------

##### `STDIN`/`STDOUT`/`STDERR` #####

Pandoc uses UTF-8 for both input and output; so must we.  Python's  sys.stdin/stdout/stderr behaviours differ between versions 3 and 4.  Use these instead.


Actions
-------

Preprocessing and postprocessing functions.


### References ###

pandocfiltering provides support for reading and processing references like `{+@label:id}`.  The curly brackets and `+` modifier are optional.  This is used, for example, by the [pandoc-fignos] filter to process references to figures.

[pandoc-fignos]: https://github.com/tomduck/pandoc-fignos


##### `repair_refs(key, value, fmt, meta)` #####

Repairs broken references.  Using `-f markdown+autolink_bare_uris` splits braced references like `{@label:id}` at the `:` into `Link` and `Str` elements.  This function replaces the mess with the `Cite` and `Str` elements normally found.  Call this action before any reference processing.


##### `use_refs_factory(references)` #####

Returns `use_refs(key, value, fmt, meta)` function that replaces known `references` with `Ref` elements.  `Ref` elements aren't understood by pandoc, but are easily identified for further processing by a filter.

The `Ref` element has four values: the attributes, prefix, reference string, and suffix.


### Images ###

The `Image` element became attributed in pandoc 1.16.  These functions help support earlier versions of pandoc.


##### `use_attrimages(key, value, fmt, meta)` #####

Substitutes `AttrImage` elements for all attributed images (pandoc<1.16).  `AttrImage` is the same as `Image` for pandoc>=1.16.  Unattributed images are left untouched.


##### `filter_attrimages(key, value, fmt, meta)` #####

Replaces all AttrImage elements with Image elements (pandoc<1.16).


Functions
---------

### Metadata Processing ###

##### `get_meta(meta, name)` #####

Retrieves the metadata variable `name` from the dict `meta`.


### Attribute Processing ###

These functions provide support for processing of attributes strings that are otherwise ignored by pandoc.  See also the [pandoc-attributes] module by @aaren.

[pandoc-attributes]: https://github.com/aaren/pandoc-attributes


##### `extract_attrs(value, n)` #####

Extracts attributes from a `value` list beginning at index `n`.

Extracted elements are set to `None` in the `value` list.
    
Returns the attributes in pandoc format.  A `ValueError` is raised if attributes aren't found.


### String Processing ###

The following functions are intended to be used together with `stringify()` from pandocfilters.


##### `quotify(x)` #####

Replaces `Quoted` elements with quoted strings.

Pandoc uses the `Quoted` element in its json when `--smart` is enabled.  Output to TeX/pdf automatically triggers `--smart`.

`stringify()` ignores `Quoted` elements.  Use `quotify()` first to replace `Quoted` elements in `x` with quoted strings.  You should provide a deep copy of `x` so that the document is left untouched.

Returns `x`.


##### `dollarfy(x)` #####

Replaces Math elements with a $-enclosed string.

`stringify()` passes through TeX math.  Use `dollarfy(x)` first to replace `Math` elements with math strings set in dollars.  You should provide a deep copy of `x` so that the document is left untouched.

Returns `x`.


##### `pandocify(s)` #####

Returns a representation of the string `s` using pandoc elements.
Like `stringify()`, all formatting is ignored.


Decorators
----------

##### `@filter_null` #####

Removes `None` values from the value list.

Suppose that `func(value, ...)` is used to process a value list.  Instead of deleting items, you can decorate `func()` with `@filter_null` and replace the items with `None` instead.  The decorator will remove all null items from the value list before it returns the result of the function call.  The filtering is done *in place*.

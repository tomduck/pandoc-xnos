

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


##### `STRTYPES` #####

Python 2 and 3 have different string types.  This constant lists what is available.


Streams
-------

##### `STDIN`/`STDOUT`/`STDERR` #####

Pandoc uses UTF-8 for both input and output; so must we.  Python's  sys.stdin/stdout/stderr behaviours differ between versions 3 and 4.  Use these instead.


Actions and Factory Functions
-----------------------------

### References ###

pandocfiltering provides support for reading and processing references like `{+@label:id}`.  The curly brackets and `+` modifier are optional.  This is used, for example, by the [pandoc-fignos] filter to process figure references.

[pandoc-fignos]: https://github.com/tomduck/pandoc-fignos


##### `repair_refs(key, value, fmt, meta)` #####

Using `-f markdown+autolink_bare_uris` splits braced references like `{@label:id}` at the `:` into `Link` and `Str` elements.  This function replaces the mess with the `Cite` and `Str` elements normally found.  Call this action before any reference processing.


##### `use_refs_factory(references)` #####

Returns `use_refs(key, value, fmt, meta)` function that replaces known `references` with `Ref` elements.  `Ref` elements aren't understood by pandoc, but are easily identified for further processing by a filter (such as is produced by `replace_refs_factory()`).


##### `replace_refs_factory(references, cleveref_default, plusname, starname)` #####

Returns `replace_refs(key, value, fmt, meta)` function that replaces
`Ref` elements with text.  The text is provided by the `references` dict.  Clever referencing is used if `cleveref_default` is `True`, or if "modifier" in the `Ref`'s attributes is "+" or "*".  `plusname` and `starname` are lists that give the singular and plural names for "+" and "*" clever references, respectively.


##### joinstrings(key, value, fmt, meta) #####
Joins adjacent `Str` elements.  Use this as the last action to get json like pandoc would normally produce.


### Attributes ###

Pandoc only supports attributes for a select few elements.  The following actions allow attributes to be attached, and later filtered, for any element.


##### `use_attrs_factory(name, extract_attrs=extract_attrs, allow_space=False)` #####

Returns `use_attrs(key, value, fmt, meta)` action that attaches attributes to elements of type name found in Para and Plain blocks.

The `extract_attrs()` function should read the attributes and raise a `ValueError` or `IndexError` if attributes are not found.


##### `filter_attrs_factory(name, n)` #####

Returns `filter_attrs(key, value, fmt, meta)` action that replaces named elements with unattributed versions of standard length `n`.


Functions
---------

### Metadata Processing ###

##### `get_meta(meta, name)` #####

Retrieves the metadata variable `name` from the dict `meta`.


### Attribute Processing ###

These functions provide support for processing of attributes strings that are otherwise ignored by pandoc.  See also the [pandoc-attributes] module by [@aaren].

[pandoc-attributes]: https://github.com/aaren/pandoc-attributes
[@aaren]: https://github.com/aaren


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

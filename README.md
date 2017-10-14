[![Travis](https://img.shields.io/travis/Erotemic/xdoctest.svg)](https://travis-ci.org/Erotemic/xdoctest)
[![Pypi](https://img.shields.io/pypi/v/xdoctest.svg)](https://pypi.python.org/pypi/xdoctest)
[![Codecov](https://codecov.io/github/Erotemic/xdoctest/badge.svg?branch=master&service=github)](https://codecov.io/github/Erotemic/xdoctest?branch=master)

## Purpose

The `xdoctest` package is a re-write of Python's builtin `doctest` module. 
It replaces the old regex-based parser with a new abstract-syntax-tree based
parser (using Python's `ast` module). 


## Enhancements 

The main enhancements `xdoctest` offers over `doctest` are:

1. All lines in the doctest can now be prefixed with `>>>`. There is no need
   for the developer to differentiate between `PS1` and `PS2` lines. However,
   old-style doctests where `PS2` lines are prefixed with `...` are still valid.
2. Additionally, the multi-line strings don't require any prefix (but its ok if
   they do have either prefix).
3. Tests are executed in blocks, rather than line-by-line, thus comment-based
   directives (e.g. `# doctest: +SKIP`) are now applied to an entire block,
   rather than just a single line.
4. Tests without a "want" statement will ignore any stdout / final evaluated
   value.  This makes it easy to use simple assert statements to perform checks
   in code that might write to stdout.
5. If your test has a "want" statement and ends with both a value and stdout,
   both are checked, and the test will pass if either matches.


## Examples

Here is an example demonstrating the new relaxed (and backwards-compatible)
syntax:

```python
def func():
    """
    # Old way
    >>> def func():
    ...     print('The old regex-based parser required specific formatting')
    >>> func()
    The old regex-based parser required specific formatting

    # New way
    >>> def func():
    >>>     print('The new ast-based parser lets you prefix all lines with >>>')
    >>> func()
    The new ast-based parser lets you prefix all lines with >>>
    """
```

```python
def func():
    """
    # Old way
    >>> print('''
    ... It would be nice if we didnt have to deal with prefixes
    ... in multiline strings.
    ... '''.strip())
    It would be nice if we didnt have to deal with prefixes
    in multiline strings.

    # New way
    >>> print('''
        Multiline can now be written without prefixes.
        Editing them is much more natural.
        '''.strip())
    Multiline can now be written without prefixes.
    Editing them is much more natural.

    # This is ok too
    >>> print('''
    >>> Just prefix everything with >>> and the doctest should work
    >>> '''.strip())
    Just prefix everything with >>> and the doctest should work

    """
```

## Google style doctest support

Additionally, this module is written using
[Google-style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/)
docstrings, and as such, the module was originally written to directly utilize
them.  However, for backwards compatibility and ease of integration into
existing software, the pytest plugin defaults to using the more normal
"freestyle" doctests that can be found anywhere in the code.

To make use of Google-style docstrings, pytest can be run with the option
`--xdoctest-style=google`, which causes xdoctest to only look for doctests in
Google "docblocks" with an `Example:` or `Doctest:` tag.

## Current Limitations and TODO:

This module is in a working state and can be used, but it is still under
development.

The main backwards-compatibility limitation is that xdoctest currently does not
have support for the `# doctest: +ELLIPSES` directive.

#### Parsing:
- [x] Parse freeform-style doctest examples
- [x] Parse google-style doctest examples
- [ ] Parse numpy-style doctest examples

#### Checking:
- [x] Support got/want testing with stdout.
- [x] Support got/want testing with evaluated statements.
- [ ] Support advanced got/want directives for backwards compatibility (e.g. ELLIPSES)

#### Reporting:
- [x] Optional colored output
- [ ] Support advanced got/want reporting directive for backwards compatibility (e.g udiff, ndiff)

#### Running:
- [x] Standalone `doctest_module` entry point.
- [x] Plugin based `pytest` entry point.

#### Testing:
- [x] Tests of core module components
- [x] Register on pypi
- [x] CI-via Travis 
- [ ] CI-via AppVeyor
- [x] Coverage
- [ ] Figure out why coverage isn't being run by the CI

#### Documentation / Misc:
- [ ] Improve readme
- [ ] Auto-generate read-the-docs Documentation
- [ ] allow for inline directives (e.g. `# doctest: +SKIP`)
- [ ] Rename to something better than `xdoctest`?

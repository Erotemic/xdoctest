[![Travis](https://img.shields.io/travis/Erotemic/xdoctest/master.svg?label=Travis%20CI)](https://travis-ci.org/Erotemic/xdoctest)
[![Codecov](https://codecov.io/github/Erotemic/xdoctest/badge.svg?branch=master&service=github)](https://codecov.io/github/Erotemic/xdoctest?branch=master)
[![Appveyor](https://ci.appveyor.com/api/projects/status/github/Erotemic/xdoctest?svg=True)](https://ci.appveyor.com/project/Erotemic/xdoctest/branch/master)
[![Pypi](https://img.shields.io/pypi/v/xdoctest.svg)](https://pypi.python.org/pypi/xdoctest)


## Purpose

The `xdoctest` package is a re-write of Python's builtin `doctest` module.  It
replaces the old regex-based parser with a new abstract-syntax-tree based
parser (using Python's `ast` module). The goal is to make doctests easier to
write, simpler to configure, and encourage the pattern of test driven
development.

## Installation

#### From pypi
```
pip install xdoctest
```

#### From github (bleeding edge)
```
pip install git+git://github.com/Erotemic/xdoctest.git@master
```

## Usage

### With pytest interface

When `pytest` is run, `xdoctest` is automatically discovered, but it disabled
by default. This is because `xdoctest` needs to replace the builtin `doctest`
plugin.

To enable this plugin, run pytest with `--xdoctest` or `--xdoc`. This should be
added to your `addopts` options in the `[pytest]` section of your `pytest.ini`
or `tox.ini` if you use one.

To run a specific doctest, `xdoctest` sets up pytest node names for these
doctests using the following pattern: `<path/to/file.py>::<callname>:<num>`.
For example a doctest for a function might look like this
`mymod.py::funcname:0`, and a class method might look like this:
`mymod.py::ClassName::method:0`


### With the native interface. 

The `xdoctest` module contains a `pytest` plugin, but also contains a native
interface. This interface is run programmatically using
`xdoctest.doctest_module(path)`, which can be placed in the `__main__` section
of any module as such:


```python
if __name__ == '__main__':
    import xdoctest as xdoc
    xdoc.doctest_module(__file__)
```

This sets up the ability to invoke the `xdoctest` command line interface.
`python -m <modname> <command>`

If `<command>` is `all`, then each enabled doctest in the module is executed:
`python -m <modname> all`

If `<command>` is `list`, then the names of each enabled doctest is listed.

If `<command>` is a `callname` (name of a function or a class and method), then
that specific doctest is executed: `python -m <modname> <callname>`. Note: you
can execute disabled doctests or functions without any arguments this way.


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


## Notes on Got/Want tests

The new got/want tester is very permissive by default; it ignores differences
in whitespace, tries to normalize for python 2/3 Unicode/bytes differences,
ANSI formatting, and it uses the old doctest ELLIPSIS fuzzy matcher by default.
If the "got" text matches the "want" text at any point, the test passes.

Currently, this permissiveness is not highly configurable as it was in the
original doctest module. It is an open question as to whether or not this
module should support that level of configuration.  If the test requires a high
degree of specificity in the got/want checker, it may just be better to use an
`assert` statement.


## Current Limitations and TODO:

This module is in a working state and can be used, but it is still under
development.

#### Parsing:
- [x] Parse freeform-style doctest examples
- [x] Parse google-style doctest examples
- [ ] Parse numpy-style doctest examples

#### Checking:
- [x] Support got/want testing with stdout.
- [x] Support got/want testing with evaluated statements.
- [x] Support got/want testing with `NORMALIZED_WHITESPACE` and `ELLIPSES` by default
- [ ] Support toggling got/want directives for backwards compatibility?

#### Reporting:
- [x] Optional colored output

#### Running:
- [x] Standalone `doctest_module` entry point.
- [x] Plugin based `pytest` entry point.

#### Testing:
- [x] Tests of core module components
- [x] Register on pypi
- [x] CI-via Travis 
- [x] CI-via AppVeyor
- [x] Coverage
- [ ] 95% or better coverage (note reported coverage is artificially small due to issues with coverage of pytest plugins)

#### Documentation:
- [x] Basic docstring docs
- [ ] Auto-generate read-the-docs Documentation
- [x] Basic readme
- [ ] Improve readme

#### Undecided:
- [ ] allow for inline directives (e.g. `# doctest: +SKIP`)?
- [ ] Rename to something better than `xdoctest`?
- [ ] Support advanced got/want reporting directive for backwards compatibility (e.g udiff, ndiff)?

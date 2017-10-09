[![Travis](https://img.shields.io/travis/Erotemic/xdoctest.svg)](https://travis-ci.org/Erotemic/xdoctest)
[![Pypi](https://img.shields.io/pypi/v/xdoctest.svg)](https://pypi.python.org/pypi/xdoctest)
[![Codecov](https://codecov.io/github/Erotemic/xdoctest/badge.svg?branch=master&service=github)](https://codecov.io/github/Erotemic/xdoctest?branch=master)

## Purpose

The `xdoctest` package is a re-write of Python's builtin `doctest` module. 
It replaces the old regex-based parser with a new abstract-syntax-tree based
parser (using Python's `ast` module). 

The main effects are 

1. All lines in the doctest can now be prefixed with `>>>`. 
2. Tests are executed in blocks, rather than line-by-line.


## Differences with doctest

Overall, the goal is to be "mostly" backwards compatible with doctest.
Currently not all features (such as comment-based macros) and fuzzy "want"
parsing available.

Also changed:

1. You no longer need a "want" statement. You can use simple asserts.


All together this means:

1. There is no need to carefully prefix some lines with `>>>` and others with
   `...`. (Though the latter still works)

2. Printing to stdout in the middle of a test will no longer require you to immediately write a "want" statement. 

3. If you dont specify a want statment, Also, if you don't specify a want 



## OLD README
This is a followup to pytest#2786.

This is a work in progress:

TODO:

- [x] Basic functionality
- [x] Basic got/want support
- [x] Parse google-style examples
- [ ] Parse numpy-style examples
- [x] Support for non-nested doctests? (maybe as an option)
- [ ] Add more fuzzy want support to mirror original doctest. (ELLIPSES, etc...)
- [ ] Get standalone module / package tester working
- [x] Get pytest plugin working
- [x] TESTS TESTS TESTS
- [x] Register on pypi
- [ ] CI-via Travis / AppVeyor
- [ ] Coverage
- [ ] Professional readme (remove/rephrase my ramblings)
- [ ] Documentation
- [ ] Rename to something better than `xdoctest`?

The overall goal of this module is to make doctests easier to write.

This is done by (1) allowing `>>> ` to be a valid prefix for all lines, and
(2) allowing for triple-quote multi-line strings to be written without any
prefix. These ideas are described in more detail below.


Here is an example demonstrating the proposed change: (note that both methods
are valid in the proposed method, but only the first is valid in the existing
version)
```python
def func():
    """
    # Old way
    >>> def func():
    ...     print('we used to be slaves to regexes')
    >>> func()
    we used to be slaves to regexes

    # New way
    >>> def func():
    >>>     print('but now we can write code like humans')
    >>> func()
    but now we can write code like humans
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


Because this is a complete rewrite, we can remove some backwards compatibility
assumptions. Namely, expressions are no longer executed individually. Instead
all expressions before a "want" statement will be executed as a block. This
will cause the execution of the doctest to mirror how it would proceed if you
were to copy and paste the code into an IPython terminal.

Note: The module now contains functionality to be backwards compatible with
these type of statements. However, we only check evaluated values if a want
statement follows an expression, and the stdout want is given priority over an
evaluated want.

~~As such, all "want" statements must go through stdout. So you can no longer 
do something like~~

```python
>>> 1 + 2
3
```

~~The rational for removing this feature is to encourage coders to write doctests
like "real code". In the previous example `1 + 2`  would be evaluated and
nothing would happen to it. You would never write code like that when scripting
a file and then expect its output to be something specific (at most you would
simply expect it not to throw an exception). If you were writing "real code"
you would instead write something like this:~~

```python
>>> print(1 + 2)
3
```

~~Restricting the doctests "want magic" to stdout makes it very explicit as to
what is being tested and what is not. You can even throw in simple informative
print in stdout and restrict a "want" statement to only a specific print
statement using the doctest Ellipses:~~

```python
>>> print('just printing some debug info')
>>> print('please dont fail because of me')
...
>>> print(1 + 2)
3
```

The new implementation will only throw a `want != got` error iff a want
statement was given. Thus, if you choose to write your doctest without "want
magic", then you would write your code exactly as if you were writing a normal
test:

```python
>>> print('just printing some debug info')
>>> print('please dont fail because of me')
>>> assert (1 + 2) == 3
```

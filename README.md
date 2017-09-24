This is a followup to pytest#2786.

This is a work in progress:

TODO:

- [x] Basic functionality
- [x] Basic got/want support
- [x] Parse google-style examples
- [ ] Parse numpy-style examples
- [ ] Support for non-nested doctests? (maybe as an option)
- [ ] Add more fuzzy want support to mirror original doctest.
- [ ] Get standalone module / package tester working
- [ ] Get pytest plugin working
- [ ] TESTS TESTS TESTS
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

As such, all "want" statements must go through stdout. So you can no longer 
do something like

```python
>>> 1 + 2
3
```

The rational for removing this feature is to encourage coders to write doctests
like "real code". In the previous example `1 + 2`  would be evaluated and
nothing would happen to it. You would never write code like that when scripting
a file and then expect its output to be something specific (at most you would
simply expect it not to throw an exception). If you were writing "real code"
you would instead write something like this:

```python
>>> print(1 + 2)
3
```

Restricting the doctests "want magic" to stdout makes it very explicit as to
what is being tested and what is not. You can even throw in simple informative
print in stdout and restrict a "want" statement to only a specific print
statement using the doctest Ellipses:

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

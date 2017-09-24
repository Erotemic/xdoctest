The overall goal of this module is to make doctests easier to write.

This is done by (1) allowing `>>> ` to be a valid prefix for all lines, and
(2) allowing for triple-quote multi-line strings to be written without any
prefix. These ideas are described in more detail below.



Here is an example demonstrating the proposed change: (note that both methods are valid in the proposed method, but only the first is valid in the existing version)
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

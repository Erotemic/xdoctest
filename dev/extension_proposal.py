"""
I'm thinking about extending #xdoctest. My thought is that lack of docstring syntax highlighting and the mandatory >>> are the greatest barriers to entry. Editors must address the former, but xdoctest could address the later.

Currently a google-style doctest looks like this

Example:
    >>> nums = [104, 101, 108, 108, 111, 32, 119, 111, 114, 108, 100]
    >>> chrs = list(map(chr, nums))
    >>> text = ''.join(chrs)
    >>> assert len(text) == 11, 'I like asserts better than got/want checks'
    >>> print(text)
    hello world

But perhaps it could look like this

Example:
    nums = [104, 101, 108, 108, 111, 32, 119, 111, 114, 108, 100]
    chrs = list(map(chr, nums))
    text = ''.join(chrs)
    assert len(text) == 11, 'I like asserts better than got/want checks'
    print(text)

    hello world

I see two disadvantages.

First, even the editors that do support doctest highlights wont support this new
style off the bat, but it does make the darn things a lot easier to type and
work with without special editor extensions (like the ones I use in vimtk).

Second, it is hard to distinguish code inputs from expected got/want output,
and it also must exist in the context of a google-style example block.

The second case might be addressed by a less intrusive header.
We could do something IPython-like.


Example:

    In [1]:
        nums = [104, 101, 108, 108, 111, 32, 119, 111, 114, 108, 100]
        chrs = list(map(chr, nums))
        text = ''.join(chrs)
        assert len(text) == 11, 'I like asserts better than got/want checks'
        print(text)

    Out [1]:
        hello world


But I don't like the additional indentation (and I think if there is a trailing
`:`, you really ought to have indentation) , and the numbering might get
annoying. Maybe break it into two google-docstr-style blocks?


Example In[]:
    nums = [104, 101, 108, 108, 111, 32, 119, 111, 114, 108, 100]
    chrs = list(map(chr, nums))
    text = ''.join(chrs)
    assert len(text) == 11, 'I like asserts better than got/want checks'
    print(text)

Example Out[]:
    hello world


As an additional extension we could do something to support an RST-style
doctest header.

.. code:: python

    nums = [104, 101, 108, 108, 111, 32, 119, 111, 114, 108, 100]
    chrs = list(map(chr, nums))
    text = ''.join(chrs)
    assert len(text) == 11, 'I like asserts better than got/want checks'
    print(text)

    hello world

Again, the problem of distinguishing inputs / outputs persists.


2023-01-27: New idea: backticks


Syntax Idea #1: Use markdown with explicit python tags

def foobar():
    '''
    Example:
        ```python
        x = 1
        y = 2
        print(x + y)
        ```

        ```output
        3
        ```

    '''


Syntax Idea #2: Use a simplified markdown tag that is reminicent of markdown

def foobar():
    '''
    Example:
        `python
        x = 1
        y = 2
        print(x + y)

        `output
        3

    '''


Syntax Idea #3: Lead output with an xdoctest directive

def foobar():
    '''
    Example:
        # xdoctest: example
        x = 1
        y = 2
        print(x + y)

        # xdoctest: output
        3
    '''


Shorter prefixes?

def foobar():
    '''
    Example:
        > x = 1
        > y = 2
        > print(x + y)
        3
    '''


First line matters?
def foobar():
    '''
    Example:

        .. code:: python

            x = 1
            y = 2
            print(x + y)

        .. code:: output

            3
    '''

"""

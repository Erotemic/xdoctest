# From boltons

# python -m xdoctest boltons/urlutils.py OrderedMultiDict.sorted:0

# def distinguish_ellipses_from_extension():
#     """
#     This is a parsing error because how do we know if ... is an ellipses or
#     a parsing error?

#     Note, if we put a # after the empty line, the code still breaks, so that is
#     something we can/should fix.

#     >>> class NamesFilter(object):
#     ...    def __init__(self, allowed):
#     ...        self._allowed = allowed
#     ...
#     ...    def filter(self, names):
#     ...        return [name for name in names if name in self._allowed]
#     """


def known_indent_value_case():
    """
    xdoctest -m ~/code/xdoctest/dev/backwards_incompatiblity_examples_inthewild.py known_indent_value_case

    >>> b = 3
    >>> if True:
    ...     a = 1
    ...     isinstance(1, int)
    True

    """


def foo():
    """
    the b'' prefix is messing this up

    xdoctest ~/code/boltons/boltons/urlutils.py OrderedMultiDict
    xdoctest ~/code/xdoctest/dev/backwards_incompatiblity_examples_inthewild.py foo

    >>> from pprint import pprint as pp  # ensuring proper key ordering
    >>> omd = {'a': 3, 'b': 2}
    >>> pp(dict(omd))
    {'a': 3, 'b': 222}
    """


def eval_in_loop_case():
    """
    xdoctest -m ~/code/xdoctest/dev/backwards_incompatiblity_examples_inthewild.py eval_in_loop_case

    >>> for i in range(2):
    ...     '%s' % i
    ...
    '0'
    '1'
    """


def breaking():
    """
    CommandLine:
        xdoctest -m ~/code/xdoctest/dev/backwards_incompatiblity_examples_inthewild.py breaking

    Example:
        >>> from xdoctest.utils import codeblock
        >>> # Simulate an indented part of code
        >>> if True:
        >>>     # notice the indentation on this will be normal
        >>>     codeblock_version = codeblock(
        ...             '''
        ...             def foo():
        ...                 return 'bar'
        ...             '''
        ...         )
        >>>     # notice the indentation and newlines on this will be odd
        >>>     normal_version = ('''
        ...         def foo():
        ...             return 'bar'
        ...     ''')
        >>> assert normal_version != codeblock_version
        >>> print('Without codeblock')
        >>> print(normal_version)
        >>> print('With codeblock')
        >>> print(codeblock_version)
    """



def linestep():
    r"""
    CommandLine:
        xdoctest -m ~/code/xdoctest/dev/backwards_incompatiblity_examples_inthewild.py linestep

        python -m doctest ~/code/xdoctest/dev/backwards_incompatiblity_examples_inthewild.py linestep

    >>> print(r'foo\r\n')
    'foo'
    """

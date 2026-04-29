"""
This file contains doctests that work in xdoctest but fail in doctest

Use the following command lines to run the doctest and xdoctest version to see
the difference:

CommandLine:
    python -m xdoctest demo_enhancements.py
    python -m doctest demo_enhancements.py
"""


def multiline_madness():
    """
    >>> if True:
    >>>     print('doctest requires a special ... prefix')
    doctest requires a special ... prefix
    """
    pass


def embeded_triple_quotes():
    """
    >>> x = '''
        xdoctest is good at dealing with triple quoted strings
        you don't even need to have the >>> prefix, because the
        AST knows you are in a string context
        '''
    >>> print(x)
    xdoctest is good at dealing with triple quoted strings
    you don't even need to have the >>> prefix, because the
    AST knows you are in a string context
    """
    pass


def sequential_print_statements():
    """
    >>> print('In builtin doctest you have to handle stdout on EVERY line')
    >>> print('But in xdoctest its no problem')
    In builtin doctest you have to handle stdout on EVERY line
    But in xdoctest its no problem
    """
    pass


def repl_print_statements():
    """
    >>> print('but sometimes repl is good')
    but sometimes repl is good
    >>> print('thats ok, we support it')
    thats ok, we support it
    """
    pass


def multiple_eval_for_loops_v1():
    """
    Previously this failed in xdoctest, but now it works as of 0.9.1

    >>> for i in range(2):
    ...     '%s' % i
    ...
    '0'
    '1'
    """


def multiple_eval_for_loops_v2():
    """
    However, xdoctest can handle this as long as you print to stdout

    >>> for i in range(2):
    ...     print('%s' % i)
    ...
    0
    1
    """


def top_level_async():
    """
    xdoctest supports top-level async examples.

    >>> async def func():
    >>>     return 'awaited'
    >>> await func()
    'awaited'
    """


def prefixed_triple_quotes():
    """
    >>> x = '''
    >>> Prefixing every line with >>> is ok too
    >>> even inside a string literal
    >>> '''
    >>> print(x.strip())
    Prefixing every line with >>> is ok too
    even inside a string literal
    """
    pass


def assert_based_examples_can_ignore_stdout():
    """
    >>> print('debug output that is not part of the test')
    >>> value = 1 + 1
    >>> assert value == 2
    """


def block_directives():
    """
    >>> # xdoctest: +SKIP
    >>> raise AssertionError('xdoctest skips this whole block')
    """

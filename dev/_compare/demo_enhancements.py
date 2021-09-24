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


def compact_style_code():
    """
    This compact style is a bit ugly, but it should still be valid python

    Exception:
        >>> try: raise Exception  # doctest: +ELLIPSIS
        ... except Exception: raise
        Traceback (most recent call last):
        ...
        Exception
        ...

    """
    try: raise Exception  # NOQA
    except Exception: pass  # NOQA

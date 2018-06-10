"""
TODO:
    Anything that works in both should be moved into a different files to show
    commonalities, and anything that only works in one should be in another
    file to show differences.
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

# TODO: fix the higlighting of the "got" string when dumping test results


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
    This is one corner case, where doctest can do something xdoctest cannot.

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

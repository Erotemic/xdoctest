def do_asserts_work():
    """
    >>> # xdoctest: +REQUIRES(--demo-failure)
    >>> assert False, 'this test should fail'
    """
    pass


def multiline_madness():
    """
    >>> if True:
    >>>     print('I expect this')
    I expect this
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


# def sequential_print_statements():
#     """
#     >>> print('In builtin doctest you have to handle stdout on EVERY line')
#     >>> print('But in xdoctest its no problem')
#     In builtin doctest you have to handle stdout on EVERY line
#     But in xdoctest its no problem
#     """
#     pass
# FIXME: Actually it is a problem right now. I forgot that my handling of repl
# broke this feature. However, I will soon fix it. The fix will involve
# accumulating stdout and then basically checking that a stdout line is
# eventually handled, and if its not by the end of the test it fails.


def repl_print_statements():
    """
    >>> print('but sometimes repl is good')
    but sometimes repl is good
    >>> print('thats ok, we support it')
    thats ok, we support it
    """
    pass

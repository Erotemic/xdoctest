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

    Not sure if we can do anything about this

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

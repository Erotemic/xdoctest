"""
Define errors that may be raised by xdoctest
"""


class MalformedDocstr(Exception):
    """
    Exception raised when the docstring itself does not conform to the expected
    style (e.g. google / numpy).
    """
    pass


class DoctestParseError(Exception):
    """
    Exception raised when doctest code has an error.
    """
    def __init__(self, msg, string=None, info=None, orig_ex=None):
        super(DoctestParseError, self).__init__(msg)
        self.msg = msg
        self.string = string
        self.info = info
        self.orig_ex = orig_ex


class ExitTestException(Exception):
    pass


class IncompleteParseError(SyntaxError):
    """
    Used when something goes wrong in the xdoctest parser
    """
    pass

try:
    import _pytest
    import _pytest.outcomes
except ImportError:  # nocover
    # Define dummy skipped exception if pytest is not available
    class _pytest(object):
        class outcomes(object):
            class Skipped(Exception):
                pass

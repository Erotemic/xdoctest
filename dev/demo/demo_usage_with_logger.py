"""
demo_usage_with_logger.py

Script to demo a workaround to [Issue111]_.


CommandLine:
    # Run with xdoctest runner
    xdoctest ~/code/xdoctest/dev/demo/demo_usage_with_logger.py

    # Run with pytest runner
    pytest -s --xdoctest --xdoctest-verbose=3 ~/code/xdoctest/dev/demo/demo_usage_with_logger.py

    # Run with builtin main
    python ~/code/xdoctest/dev/demo/demo_usage_with_logger.py

References:
    .. [Issue111] https://github.com/Erotemic/xdoctest/issues/111
"""

import logging
import sys


class StreamHandler2(logging.StreamHandler):
    def __init__(self, _getstream=None):
        """
        Initialize the handler.

        If stream is not specified, sys.stderr is used.
        """
        logging.Handler.__init__(self)
        if _getstream is None:
            _getstream = lambda: sys.stderr  # NOQA
        self._getstream = _getstream
        self.__class__.stream = property(lambda self: self._getstream())

    def setStream(self, stream):
        raise NotImplementedError


handler = StreamHandler2(lambda: sys.stdout)

_log = logging.getLogger('mylog')
_log.setLevel(logging.INFO)
_log.addHandler(handler)

_log.info('hello')
_log.info('hello hello')


def func_with_doctest():
    """
    Example:
        >>> _log.info('greetings from my doctest')
        greetings from my doctest
    """


def main():
    import xdoctest

    xdoctest.doctest_callable(func_with_doctest)


if __name__ == '__main__':
    main()

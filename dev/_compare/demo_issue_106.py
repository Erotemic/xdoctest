"""
    https://github.com/Erotemic/xdoctest/issues/106
    python -m xdoctest demo_issue_106.py
    python -m doctest demo_issue_106.py
"""
import sys


def logTraceback(logFunction):
    r""" Logs the exception traceback to the specified log function.

    >>> try: raise Exception()  # doctest: +ELLIPSIS
    ... except Exception: logTraceback(lambda *a, **b: sys.stdout.write(a[0] + "\n", *a[1:], **b))
    Traceback (most recent call last):
    ...
    Exception
    ...
    """
    sys.exc_info()
    import xdev
    xdev.embed()
    logFunction
    pass


# def compact_style_code():
#     """
#     This compact style is a bit ugly, but it should still be valid python

#     Exception:
#         >>> try: raise Exception  # doctest: +ELLIPSIS
#         ... except Exception: raise
#         Traceback (most recent call last):
#         ...
#         Exception
#         ...

#     """
#     try: raise Exception  # NOQA
#     except Exception: pass  # NOQA


def logTraceback2(logFunction):
    r""" Logs the exception traceback to the specified log function.

    >>> try:
    ...     raise Exception()
    ... except Exception:
    ...     logTraceback(lambda *a, **b: sys.stdout.write(a[0] + "\n", *a[1:], **b))
    Traceback (most recent call last):
    ...
    Exception
    ...
    """
    import sys
    logFunction(*sys.exec_info)
    logFunction()
    pass

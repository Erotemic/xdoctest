r"""
    https://github.com/Erotemic/xdoctest/issues/106
    cd ~/code/xdoctest/dev/_compare/
    python -m xdoctest demo_issue_106.py
    python -m doctest demo_issue_106.py

Note:
    the reason this fails is because this fails:

        compile('try: raise Exception\nexcept Exception: print', mode='single', filename="")


    In exec mode we are ok

        compile('try: raise Exception\nexcept Exception: print', mode='exec', filename="")

    This has to do with the assign ps1 line function that determines if
    we should be in exec or single mode

    Other tests


        compile('if 1:\n    a', mode='single', filename="")
        compile('if 1:\n    print', mode='single', filename="")
        compile('if 1:\n    x = 1\n    y = 2\nelse:\n    pass', mode='single', filename="")

        compile('try:\n    raise Exception\nexcept Exception:\n    pass', mode='single', filename="")
        compile('try: raise Exception\nexcept Exception: pass', mode='single', filename="")

        except Exception: print', mode='single', filename="")

"""
import sys


def logTracebackThisDoesnt(logFunction):
    r""" Logs the exception traceback to the specified log function.

    >>> # xdoctest: +IGNORE_WANT
    >>> try: raise Exception()  # doctest: +ELLIPSIS
    ... except Exception: print(lambda *a, **b: sys.stdout.write(str(a) + "\n" + str(b)))
    Traceback (most recent call last):
    ...
    Exception
    ...
    """
    sys.exc_info()
    # import xdev
    # xdev.embed()
    logFunction
    pass


# def logTracebackThisWorks(logFunction):
#     r""" Logs the exception traceback to the specified log function.

#     >>> try: raise Exception()  # doctest: +ELLIPSIS
#     >>> except Exception: print(lambda *a, **b: sys.stdout.write(str(a) + "\n" + str(b)))
#     Traceback (most recent call last):
#     ...
#     Exception
#     ...
#     """
#     sys.exc_info()
#     # import xdev
#     # xdev.embed()
#     logFunction
#     pass

#     # ... except Exception: logTraceback(lambda *a, **b: sys.stdout.write(a[0] + "\n", *a[1:], **b))

# # def compact_style_code():
# #     """
# #     This compact style is a bit ugly, but it should still be valid python

# #     Exception:
# #         >>> try: raise Exception  # doctest: +ELLIPSIS
# #         ... except Exception: raise
# #         Traceback (most recent call last):
# #         ...
# #         Exception
# #         ...

# #     """
# #     try: raise Exception  # NOQA
# #     except Exception: pass  # NOQA


# def logTraceback2(logFunction):
#     r""" Logs the exception traceback to the specified log function.

#     >>> try:
#     ...     raise Exception()
#     ... except Exception:
#     ...     logTraceback(lambda *a, **b: sys.stdout.write(a[0] + "\n", *a[1:], **b))
#     Traceback (most recent call last):
#     ...
#     Exception
#     ...
#     """
#     import sys
#     logFunction(*sys.exec_info)
#     logFunction()
#     pass

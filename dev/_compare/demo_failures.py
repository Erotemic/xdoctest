"""
This contains that fail in both. This demos what correct
failures look like in each case.

CommandLine:
    python -m xdoctest demo_failures.py
    python -m doctest demo_failures.py
"""


def do_asserts_work():
    """
    >>> assert False, 'this test should fail'
    """
    pass


def multiple_eval_for_loops_v1_fail():
    """

    >>> for i in range(2):
    ...     '%s' % i
    ...
    0
    1
    """

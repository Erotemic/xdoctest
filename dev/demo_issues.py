def demo_requires_skips_all_v1():
    """
    Example:
        >>> # xdoctest: +REQUIRES(--cliflag)
        >>> print('hello world')
    """


def demo_requires_skips_all_v2():
    """
    Example:
        >>> # xdoctest: +REQUIRES(module:xdoctest)
        >>> # xdoctest: +REQUIRES(--cliflag)
        >>> print('hello world')
    """


def demo():
    """
    CommandLine:

        # Correctly reports skipped (although an only skipped test report
        # should probably be yellow)
        xdoctest -m dev/demo_issues.py demo_requires_skips_all_v1

        # Incorrectly reports success
        xdoctest -m dev/demo_issues.py demo_requires_skips_all_v2

        # Correctly reports success
        xdoctest -m dev/demo_issues.py demo_requires_skips_all_v2 --cliflag

        # Correctly reports success
        xdoctest -m dev/demo_issues.py demo_requires_skips_all_v1 --cliflag
    """

    # Programatic reproduction (notice the first one also reports itself in
    # pytest mode which is also wrong)
    import xdoctest
    xdoctest.doctest_callable(demo_requires_skips_all_v1)
    xdoctest.doctest_callable(demo_requires_skips_all_v2)

    import sys, ubelt
    sys.path.append(ubelt.expandpath('~/code/xdoctest/dev'))
    import demo_issues

    # Correctly reports skipped
    xdoctest.doctest_module(demo_issues, command='demo_requires_skips_all_v1', argv=[])

    # Incorrectly reports passed
    xdoctest.doctest_module(demo_issues, command='demo_requires_skips_all_v2', argv=[])

    # argv not respected?
    xdoctest.doctest_module(demo_issues, command='demo_requires_skips_all_v1', argv=['--cliflag'])

    # argv not respected?
    xdoctest.doctest_module(demo_issues, command='demo_requires_skips_all_v2', argv=['--cliflag'])

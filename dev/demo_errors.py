#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains doctests with errors. Executing xdoctest on this file will
demo how xdoctest reoprts errors. (It can also be used / was created for
debuging)
"""
from __future__ import absolute_import, division, print_function, unicode_literals


def demo1():
    """
    CommandLine:
        xdoctest -m ~/code/xdoctest/dev/demo_errors.py demo1

    Example:
        >>> raise Exception('demo1')
    """
    pass


def demo2():
    """
    CommandLine:
        xdoctest -m ~/code/xdoctest/dev/demo_errors.py demo2

    Example:
        >>> print('error on different line')
        >>> raise Exception('demo2')
    """
    pass


def demo3():
    """
    CommandLine:
        xdoctest -m ~/code/xdoctest/dev/demo_errors.py demo3

    Example:
        >>> print('demo5')
        demo3
    """
    pass


class Demo5(object):
    """
    CommandLine:
        xdoctest -m ~/code/xdoctest/dev/demo_errors.py Demo5

    Example:
        >>> raise Exception
    """
    def demo5(self):
        """
        CommandLine:
            xdoctest -m ~/code/xdoctest/dev/demo_errors.py Demo5.demo5

        Example:
            >>> raise Exception
        """
        pass


def demo_parsetime_syntax_error1():
    """
    Example:
        >>> from __future__ import print_function
        >>> print 'Parse-Time Syntax Error'
    """


def demo_parsetime_syntax_error2():
    """
    Example:
        >>> def bad_syntax() return for
    """


def demo_runtime_error():
    """
    Example:
        >>> print('Runtime Error {}'.format(5 / 0))
    """


def demo_runtime_name_error():
    """
    Example:
        >>> print('Name Error {}'.format(foo))
    """


def demo_runtime_warning():
    """
    Example:
        >>> import warnings
        >>> warnings.warn('in-code warning')
    """


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdoctest/dev/demo_errors.py all
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

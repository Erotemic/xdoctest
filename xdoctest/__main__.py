#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a simple script for running module doctests.

This should work even if the target module is unaware of xdoctest.
"""
from __future__ import absolute_import, division, print_function, unicode_literals


def main():
    """
    python -m xdoctest xdoctest all
    python -m xdoctest networkx all
    """
    import xdoctest
    import sys
    argv = sys.argv[1:]
    if len(argv) == 0:
        raise ValueError('Supply xdoctest with a module name or path')
    # Must supploy
    #     # test self
    #     modname = 'xdoctest'
    #     argv = ['', 'all']
    # else:
    modname = argv[0]
    argv = argv[1:]

    # xdoctest.doctest_module(modname, command='all', argv=argv, style='freeform')
    xdoctest.doctest_module(modname, argv=argv, style='freeform')


if __name__ == '__main__':
    main()

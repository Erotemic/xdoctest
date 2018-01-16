#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals


def main():
    """
    python -m xdoctest xdoctest
    python -m xdoctest networkx
    """
    import xdoctest
    import sys
    argv = sys.argv[1:]
    if len(argv) == 0:
        # test self
        modname = 'xdoctest'
        argv = ['', 'all']
    else:
        modname = argv[0]
    argv = argv[1:]

    # xdoctest.doctest_module(modname, command='all', argv=argv, style='freeform')
    xdoctest.doctest_module(modname, argv=argv, style='freeform')


if __name__ == '__main__':
    main()

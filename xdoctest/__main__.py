#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals


def main():
    import xdoctest
    import sys
    argv = sys.argv[1:]
    if len(sys.argv) == 1:
        modname = 'xdoctest'
    else:
        modname = argv[0]

    xdoctest.doctest_module(modname, command='all', argv=[])


if __name__ == '__main__':
    main()

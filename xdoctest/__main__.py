#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals


def main():
    import xdoctest
    modname = 'xdoctest'
    xdoctest.doctest_module(modname)


if __name__ == '__main__':
    main()

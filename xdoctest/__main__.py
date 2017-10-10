#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals


def main():
    import sys
    from xdoctest import core
    package = sys.argv[1]
    core.doctest_package(package)


if __name__ == '__main__':
    main()

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
    # TODO: argparse
    import ubelt as ub
    import argparse
    description = ub.codeblock(
        '''
        This is the description
        ''')

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('argv', nargs='*', help='What do?')
    parser.add_argument(*('--style',), type=str, help='choose your style',
                        default='freeform')
    args = parser.parse_args()
    ns = args.__dict__.copy()

    # ... postprocess args

    # import sys
    # argv = sys.argv[1:]

    argv = ns['argv']
    if len(argv) == 0:
        raise ValueError('Supply xdoctest with a module name or path')
    modname = argv[0]
    argv = argv[1:]

    style = ub.argval('--style', default=ns['style'])

    import xdoctest
    # xdoctest.doctest_module(modname, command='all', argv=argv, style='freeform')
    # xdoctest.doctest_module(modname, argv=argv, style='freeform')
    xdoctest.doctest_module(modname, argv=argv, style=style)


if __name__ == '__main__':
    main()

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
    python -m xdoctest networkx all --options=+IGNORE_WHITESPACE
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
    parser.add_argument(*('--options',), type=str,
                        help='specify the default directive state',
                        default=None)
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

    if ns['options'] is None:
        from os.path import exists
        ns['options'] = ''
        if exists('pytest.ini'):
            from six.moves import configparser
            parser = configparser.ConfigParser()
            parser.read('pytest.ini')
            try:
                ns['options'] = parser.get('pytest', 'xdoctest_options')
            except configparser.NoOptionError:
                pass

    from xdoctest.directive import parse_directive_optstr
    default_runtime_state = {}
    for optpart in ns['options'].split(','):
        if optpart:
            directive = parse_directive_optstr(optpart)
            if directive is not None:
                default_runtime_state[directive.name] = directive.positive

    config = {
        'default_runtime_state': default_runtime_state
    }

    import xdoctest
    xdoctest.doctest_module(modname, argv=argv, style=style, config=config)


if __name__ == '__main__':
    main()

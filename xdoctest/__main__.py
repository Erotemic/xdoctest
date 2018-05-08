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
    import argparse
    from xdoctest import utils
    description = utils.codeblock(
        '''
        discover and run doctests within a python package
        ''')

    parser = argparse.ArgumentParser(prog='python -m xdoctest', description=description)
    parser.add_argument('modname', help='what files to run')
    parser.add_argument('command', help='a doctest name or a command (list|all)', default='list')
    parser.add_argument(*('--style',), type=str, help='choose your style',
                        default='freeform')
    parser.add_argument(*('--options',), type=str,
                        help='specify the default directive state',
                        default=None)

    args, unknown = parser.parse_known_args()
    ns = args.__dict__.copy()

    # ... postprocess args
    modname = ns['modname']
    command = ns['command']
    style = ns['style']

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
    xdoctest.doctest_module(modname, argv=[command], style=style, config=config)


if __name__ == '__main__':
    main()

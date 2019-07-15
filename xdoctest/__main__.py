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
    import sys
    import argparse
    from os.path import exists
    from xdoctest import utils

    parser = argparse.ArgumentParser(
        prog='xdoctest',
        description=utils.codeblock(
            '''
            discover and run doctests within a python package
            ''')
    )
    # parser.add_argument('modname', help='what files to run')
    # parser.add_argument('command', help='a doctest name or a command (list|all)', default='list')
    parser.add_argument(
        'arg', nargs='*', help=utils.codeblock(
            '''
            Ignored if optional arguments are specified, otherwise:
            Defaults --modname to arg.pop(0).
            Defaults --command to arg.pop(0).
            '''))

    # modname_or_path_group = parser.add_mutually_exclusive_group()
    # modname_or_path_group.add_argument('modpath', help='module name or path')
    # parser.add_argument(*('-m', '--modname'), type=str,
    #                     help='module name or path. If specified positional modules are ignored',
    #                     default=None)

    # parser.add_argument(*('-c', '--command'), type=str,
    #                     help='a doctest name or a command (list|all|<callname>). '
    #                     'Defaults to all',
    #                     default=None)

    # parser.add_argument(*('--style',), type=str, help='choose your style',
    #                     choices=['auto', 'google', 'freeform'], default='auto')

    from xdoctest import doctest_example
    from xdoctest import runner
    runner._update_argparse_cli(parser.add_argument)
    doctest_example.Config()._update_argparse_cli(parser.add_argument)

    # parser.add_argument(*('--options',), type=str,
    #                     help='specify the default directive state',
    #                     default=None)

    # parser.add_argument(*('--offset',), dest='offset_linenos', action='store_true',
    #                     help=('Doctest outputs will display line numbers '
    #                           'wrt to the source file.'))

    # parser.add_argument(*('--nocolor',), dest='colored', action='store_true',
    #                     help=('Disable ANSI coloration.'))

    # parser.add_argument(*('--durations',), type=int,
    #                     help=('specify execution times for slowest N tests.'
    #                           'N=0 will show times for all tests'),
    #                     default=None)

    # parser.add_argument(*('--time',), dest='time', action='store_true',
    #                     help=('Same as if durrations=0'))

    args, unknown = parser.parse_known_args()
    ns = args.__dict__.copy()

    # ... postprocess args
    modname = ns['modname']
    command = ns['command']
    arg = ns['arg']
    style = ns['style']
    durations = ns['durations']
    if ns['time']:
        durations = 0
    # ---
    # Allow for positional args to specify defaults for unspecified optionals
    errors = []
    if modname is None:
        if len(arg) == 0:
            errors += ['you must specify modname or modpath']
        else:
            modname = arg.pop(0)

    if command is None:
        if len(arg) == 0:
            # errors += ['you must specify a command e.g (list, all)']
            command = 'all'
        else:
            command = arg.pop(0)

    if errors:
        if len(errors) == 1:
            errmsg = errors[0]
        else:
            listed_errors = ', '.join(['({}) {}'.format(c, e)
                                       for c, e in enumerate(errors, start=1)])
            errmsg = '{} errors: {}'.format(len(errors), listed_errors)
        parser.error(errmsg)
    # ---

    import xdoctest

    options = ns['options']
    if options is None:
        options = ''
        if exists('pytest.ini'):
            from six.moves import configparser
            parser = configparser.ConfigParser()
            parser.read('pytest.ini')
            try:
                options = parser.get('pytest', 'xdoctest_options')
            except configparser.NoOptionError:
                pass
        ns['options'] = options
    from xdoctest import doctest_example
    config = doctest_example.Config()._populate_from_cli(ns)

    # from xdoctest.directive import parse_directive_optstr
    # default_runtime_state = {}
    # for optpart in options.split(','):
    #     if optpart:
    #         directive = parse_directive_optstr(optpart)
    #         if directive is not None:
    #             default_runtime_state[directive.name] = directive.positive

    # # Specify a default doctest_example.Config state
    # config = {
    #     'default_runtime_state': default_runtime_state,
    # offset_linenos = ns['offset_linenos']
    #     'offset_linenos': offset_linenos,
    # colored = ns['colored']
    #     'colored': colored,
    # }

    run_summary = xdoctest.doctest_module(modname, argv=[command], style=style,
                                          verbose=config['verbose'],
                                          config=config, durations=durations)
    n_failed = run_summary.get('n_failed', 0)
    if n_failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()

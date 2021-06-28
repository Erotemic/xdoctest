#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a simple script for running module doctests.

This should work even if the target module is unaware of xdoctest.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import sys


__tests = """

Ignore:

    xdoctest -m xdoctest.demo
    xdoctest ~/code/xdoctest/xdoctest/demo.py
"""


def main(argv=None):
    """
    python -m xdoctest xdoctest all
    python -m xdoctest networkx all --options=+IGNORE_WHITESPACE
    """
    import argparse
    import xdoctest
    from os.path import exists
    from xdoctest import utils

    if argv is None:
        argv = sys.argv

    version_info = {
        'version': xdoctest.__version__,
        'sys_version': sys.version,
    }

    if '--version' in argv:
        print(version_info['version'])
        return 0

    if '--version-info' in argv:
        for key, value in sorted(version_info.items()):
            print('{} = {}'.format(key, value))
        return 0

    # FIXME: default values are reporting incorrectly or are missformated
    class RawDescriptionDefaultsHelpFormatter(
            argparse.RawDescriptionHelpFormatter,
            argparse.ArgumentDefaultsHelpFormatter):
        pass

    parser = argparse.ArgumentParser(
        prog='xdoctest',
        description=(
            'Xdoctest {version} - on Python - {sys_version} - '
            'discover and run doctests within a python package'
        ).format(**version_info),
        formatter_class=RawDescriptionDefaultsHelpFormatter,
    )
    parser.add_argument(
        'arg', nargs='*', help=utils.codeblock(
            '''
            Ignored if optional arguments are specified, otherwise:
            Defaults --modname to arg.pop(0).
            Defaults --command to arg.pop(0).
            '''))
    parser.add_argument('--version', action='store_true', help='display version info and quit')

    # The bulk of the argparse CLI is defined in the doctest example
    from xdoctest import doctest_example
    from xdoctest import runner
    runner._update_argparse_cli(parser.add_argument)
    doctest_example.DoctestConfig()._update_argparse_cli(parser.add_argument)

    args, unknown = parser.parse_known_args(args=argv[1:])
    ns = args.__dict__.copy()

    __DEBUG__ = '--debug' in sys.argv
    if __DEBUG__:
        print('ns = {!r}'.format(ns))

    if ns['version']:
        print(xdoctest.__version__)
        return 0

    # ... postprocess args
    modname = ns['modname']
    command = ns['command']
    arg = ns['arg']
    style = ns['style']
    durations = ns['durations']
    analysis = ns['analysis']
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
    config = doctest_example.DoctestConfig()._populate_from_cli(ns)

    import textwrap
    if config['verbose'] > 2:
        print(textwrap.dedent(
            r'''
            =====================================
            _  _ ___  ____ ____ ___ ____ ____ ___
             \/  |  \ |  | |     |  |___ [__   |
            _/\_ |__/ |__| |___  |  |___ ___]  |

            =====================================
            '''))

    if __DEBUG__:
        try:
            import ubelt as ub
            print('config = {}'.format(ub.repr2(config)))
            print('ns = {}'.format(ub.repr2(ns)))
        except ImportError:
            pass
        print('modname = {!r}'.format(modname))

    run_summary = xdoctest.doctest_module(modname, argv=[command], style=style,
                                          verbose=config['verbose'],
                                          config=config, durations=durations,
                                          analysis=analysis)
    n_failed = run_summary.get('n_failed', 0)
    if n_failed > 0:
        return 1
    else:
        return 0


if __name__ == '__main__':
    retcode = main()
    sys.exit(retcode)

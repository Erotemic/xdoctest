# -*- coding: utf-8 -*-
"""
Native xdoctest interface to the collecting, executing, and summarizing the
results of running doctests. This is an alternative to running through pytest.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from xdoctest import dynamic_analysis as dynamic
from xdoctest import core
import sys


def doctest_module(modpath_or_name=None, command=None, argv=None, exclude=[],
                   style='google', verbose=None):
    r"""
    Executes requestsed google-style doctests in a package or module.
    Main entry point into the testing framework.

    Args:
        modname (str): name of or path to the module.
        command (str): determines which doctests to run.
            if command is None, this is determined by parsing sys.argv
        argv (list): if None uses sys.argv
        verbose (bool):  verbosity flag
        exclude (list): ignores any modname matching any of these
            glob-like patterns

    Example:
        >>> modname = 'xdoctest.dynamic_analysis'
        >>> result = doctest_module(modname, 'list', argv=[''])
    """
    print('Start doctest_module({!r})'.format(modpath_or_name))

    # Determine package name via caller if not specified
    if modpath_or_name is None:
        frame_parent = dynamic.get_parent_frame()
        modpath = frame_parent.f_globals['__file__']
    else:
        modpath = core._rectify_to_modpath(modpath_or_name)

    command, style, verbose = _parse_commandline(command, style, verbose, argv)

    if command == 'list':
        print('Listing tests')

    if command is None:
        # Display help if command is not specified
        print('Not testname given. Use `all` to run everything or')
        print('Pick from a list of valid choices:')
        command = 'list'

    run_all = (command == 'all')

    # Parse all valid examples
    examples = list(core.parse_doctestables(modpath, exclude=exclude,
                                            style=style))
    # Signal that we are not running through pytest
    for e in examples:
        e.mode = 'native'

    if command == 'list':
        if len(examples) == 0:
            print('... no docstrings with examples found')
        else:
            print('\n'.join([example.cmdline for example in examples]))
    else:
        print('gathering tests')
        enabled_examples = []
        for example in examples:
            if run_all or command in example.valid_testnames:
                if run_all and example.is_disabled():
                    continue
                enabled_examples.append(example)

        if len(enabled_examples) == 0:
            # Check for arg-less funcs
            enabled_examples += list(_zero_arg_examples(command, modpath))

        _run_examples(enabled_examples, verbose)


def _zero_arg_examples(command, modpath):
    """
    Find functions in `modpath` args that match `command` as long as they
    take no args (so we can automatically make a dummy docstring).
    """
    for calldefs, _modpath in core.package_calldefs(modpath):
        for callname, calldef in calldefs.items():
            if calldef.argnames is not None and len(calldef.argnames) == 0:
                # Create a dummy doctest example for a no-arg function
                docsrc = '>>> {}()'.format(callname)
                example = core.DocTest(docsrc=docsrc, modpath=_modpath,
                                       callname=callname, block_type='no-arg')
                if command in example.valid_testnames:
                    example.mode = 'native'
                    yield example


def _run_examples(enabled_examples, verbose):
    n_total = len(enabled_examples)
    print('running %d test(s)' % n_total)
    summaries = []
    for example in enabled_examples:
        try:
            summary = example.run(verbose=verbose)
            if not verbose:
                sys.stdout.write('.')
                sys.stdout.flush()
        except Exception:
            if not verbose:
                sys.stdout.write('F')
                sys.stdout.flush()
            print('\n'.join(example.repr_failure()))
            raise
        summaries.append(summary)
    if verbose <= 0:
        print('')
    n_passed = sum(s['passed'] for s in summaries)
    print('Finished doctests')
    print('%d / %d passed'  % (n_passed, n_total))

    return n_passed == n_total


def _parse_commandline(command, style, verbose, argv):
    # Determine command via sys.argv if not specified
    if command is None:
        if argv is None:
            argv = sys.argv
        argv = argv[1:]
        if len(argv) >= 1:
            command = argv[0]
        else:
            command = None

    # Change how docstrs are found
    if '--freeform' in sys.argv:
        style = 'freeform'
    elif '--google' in sys.argv:
        style = 'google'

    # Parse verbosity flag
    if verbose is None:
        if '--verbose' in sys.argv:
            verbose = 3
        elif '--quiet' in sys.argv:
            verbose = 0
        else:
            verbose = 2
    return command, style, verbose


if __name__ == '__main__':
    r"""
    CommandLine:
        python -m xdoctest.runner
    """
    import xdoctest as xdoc
    xdoc.doctest_module()

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
            # Check for zero-arg funcs
            for example in _gather_zero_arg_examples(modpath):
                if command in example.valid_testnames:
                    enabled_examples.append(example)

        return _run_examples(enabled_examples, verbose)


def _gather_zero_arg_examples(modpath):
    """
    Find functions in `modpath` args  with no args (so we can automatically
    make a dummy docstring).
    """
    for calldefs, _modpath in core.package_calldefs(modpath):
        for callname, calldef in calldefs.items():
            if calldef.args is not None:
                # The only existing args should have defaults
                n_args = len(calldef.args.args) - len(calldef.args.defaults)
                if n_args == 0:
                    # Create a dummy doctest example for a zero-arg function
                    docsrc = '>>> {}()'.format(callname)
                    example = core.DocTest(docsrc=docsrc, modpath=_modpath,
                                           callname=callname,
                                           block_type='zero-arg')
                    example.mode = 'native'
                    # if True:
                    #     import importlib
                    #     mod = importlib.import_module(example.modname)
                    #     getattr(mod, callname)()
                    # else:
                    yield example


def _run_examples(enabled_examples, verbose):
    n_total = len(enabled_examples)
    print('running %d test(s)' % n_total)
    summaries = []
    errors = []
    for example in enabled_examples:
        summary = None
        try:
            summary = example.run(verbose=verbose)
            if not verbose:
                sys.stdout.write('.')
                sys.stdout.flush()
        except Exception:
            summary = {'passed': False}
            if not verbose:
                sys.stdout.write('F')
                sys.stdout.flush()
            errors.append('\n'.join(example.repr_failure()))
            if len(enabled_examples) == 1:
                raise
        summaries.append(summary)
    if verbose <= 0:
        print('')
    n_passed = sum(s['passed'] for s in summaries)

    if len(enabled_examples) > 1:
        print('Finished doctests')
        print('%d / %d passed'  % (n_passed, n_total))

    if errors:
        for error in errors:
            print(error)

    return {
        'n_passed': n_passed,
        'n_total': n_total
    }


def _parse_commandline(command=None, style='google', verbose=None, argv=None):
    # Determine command via sys.argv if not specified
    if argv is None:
        argv = sys.argv[1:]

    if command is None:
        if len(argv) >= 1:
            if argv[0] and not argv[0].startswith('-'):
                command = argv[0]

    # Change how docstrs are found
    if '--freeform' in argv:
        style = 'freeform'
    elif '--google' in argv:
        style = 'google'

    # Parse verbosity flag
    if verbose is None:
        if '--verbose' in argv:
            verbose = 3
        elif '--quiet' in argv:
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

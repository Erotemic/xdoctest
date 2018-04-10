# -*- coding: utf-8 -*-
"""
Native xdoctest interface to the collecting, executing, and summarizing the
results of running doctests. This is an alternative to running through pytest.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from xdoctest import dynamic_analysis as dynamic
from xdoctest import core
from xdoctest import doctest_example
from xdoctest import utils
import time
import warnings
import sys


def doctest_module(modpath_or_name=None, command=None, argv=None, exclude=[],
                   style='google', verbose=None, config=None):
    """
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
        config (dict): modifies each examples configuration

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
        print('Not testname given. Use `all` to run everything or'
              ' pick from a list of valid choices:')
        command = 'list'

    run_all = (command == 'all')

    tic = time.time()

    # Parse all valid examples
    with warnings.catch_warnings(record=True) as parse_warnlist:
        examples = list(core.parse_doctestables(modpath, exclude=exclude,
                                                style=style))

    # Signal that we are not running through pytest
    for e in examples:
        e.mode = 'native'

    if command == 'list':
        if len(examples) == 0:
            print('... no docstrings with examples found')
        else:
            print('    ' + '\n    '.join([example.cmdline
                                          for example in examples]))
        run_summary = {'action': 'list'}
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

        if config:
            for example in enabled_examples:
                example.config.update(config)

        run_summary = _run_examples(enabled_examples, verbose)

    toc = time.time()

    # Print final summary info in a style similar to pytest
    if verbose >= 0:

        def cprint(text, color):
            print(utils.color_text(text, color))

        # report errors
        failed = run_summary.get('failed', [])
        warned = run_summary.get('warned', [])

        # report parse-time warnings
        if parse_warnlist:
            cprint('\n=== Found {} parse-time warnings ==='.format(
                len(parse_warnlist)), 'yellow')

            for warn_idx, warn in enumerate(parse_warnlist, start=1):
                cprint('--- Parse Warning: {} / {} ---'.format(
                    warn_idx, len(parse_warnlist)), 'yellow')
                print(utils.indent(
                    warnings.formatwarning(warn.message, warn.category,
                                           warn.filename, warn.lineno)))

        # report run-time warnings
        if warned:
            cprint('\n=== Found {} run-time warnings ==='.format(len(warned)), 'yellow')
            for warn_idx, example in enumerate(warned, start=1):
                cprint('--- Runtime Warning: {} / {} ---'.format(warn_idx, len(warned)),
                       'yellow')
                print('example = {!r}'.format(example))
                for warn in example.warn_list:
                    print(utils.indent(
                        warnings.formatwarning(warn.message, warn.category,
                                               warn.filename, warn.lineno)))

        if failed:
            cprint('\n=== Found {} errors ==='.format(len(failed)), 'red')
            for fail_idx, example in enumerate(failed, start=1):
                cprint('--- Error: {} / {} ---'.format(fail_idx, len(failed)), 'red')
                print(utils.indent('\n'.join(example.repr_failure())))

        # Print command lines to re-run failed tests
        if failed:
            cprint('\n=== Failed tests ===', 'red')
            for example in failed:
                print(example.cmdline)

        # final summary
        n_passed = run_summary.get('n_passed', 0)
        n_failed = run_summary.get('n_failed', 0)
        n_warnings = len(warned) + len(parse_warnlist)
        n_seconds = toc - tic
        pairs = zip([n_failed, n_passed, n_warnings],
                    ['failed', 'passed', 'warnings'])
        parts = ['{} {}'.format(n, t) for n, t in pairs  if n > 0]
        fmtstr = '=== ' + ' '.join(parts) + ' in {:.2f} seconds ==='
        summary_line = fmtstr.format(n_failed, n_passed, n_warnings, n_seconds)
        # color text based on worst type of error
        if n_failed > 0:
            summary_line = utils.color_text(summary_line, 'red')
        elif n_warnings > 0:
            summary_line = utils.color_text(summary_line, 'yellow')
        else:
            summary_line = utils.color_text(summary_line, 'green')
        print(summary_line)

    return run_summary


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
                    example = doctest_example.DocTest(docsrc=docsrc,
                                                      modpath=_modpath,
                                                      callname=callname,
                                                      block_type='zero-arg')
                    example.mode = 'native'
                    yield example


def _run_examples(enabled_examples, verbose):
    """
    Internal helper, loops over each example, runs it, returns a summary
    """
    n_total = len(enabled_examples)
    print('running %d test(s)' % n_total)
    summaries = []
    failed = []
    warned = []
    # It is important to raise immediatly within the test to display errors
    # returned from multiprocessing. Especially in zero-arg mode

    on_error = 'return' if n_total > 1 else 'raise'
    on_error = 'return'
    for example in enabled_examples:
        try:
            summary = example.run(verbose=verbose, on_error=on_error)
        except Exception:
            print('\n'.join(example.repr_failure(with_tb=False)))
            raise

        summaries.append(summary)
        if example.warn_list:
            warned.append(example)
        if summary['passed']:
            if verbose == 0:
                # TODO: should we write anything when verbose=0?
                sys.stdout.write('.')
                sys.stdout.flush()
        else:
            failed.append(example)
            if verbose == 0:
                sys.stdout.write('F')
                sys.stdout.flush()
            if on_error == 'raise':
                # What happens if we don't re-raise here?
                # If it is necessary, write a message explaining why
                print('\n'.join(example.repr_failure()))
                ex_value = example.exc_info[1]
                raise ex_value

        # except Exception:
        #     summary = {'passed': False}
        #     if verbose == 0:
        #         sys.stdout.write('F')
        #         sys.stdout.flush()
    if verbose == 0:
        print('')
    n_passed = sum(s['passed'] for s in summaries)

    print(utils.color_text('============', 'white'))

    if n_total > 1:
        # and verbose > 0:
        print('Finished doctests')
        print('%d / %d passed'  % (n_passed, n_total))

    run_summary = {
        'failed': failed,
        'warned': warned,
        'action': 'run_examples',
        'n_warned': len(warned),
        'n_passed': n_passed,
        'n_failed': n_total - n_passed,
        'n_total': n_total,
    }
    return run_summary


def _parse_commandline(command=None, style='google', verbose=None, argv=None):
    # Determine command via sys.argv if not specified
    if argv is None:
        argv = sys.argv[1:]
    else:
        print('argv = {!r}'.format(argv))

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
        elif '--silent' in argv:
            verbose = -1
        else:
            verbose = 3
    return command, style, verbose


if __name__ == '__main__':
    r"""
    CommandLine:
        python -m xdoctest.runner
    """
    import xdoctest as xdoc
    xdoc.doctest_module()

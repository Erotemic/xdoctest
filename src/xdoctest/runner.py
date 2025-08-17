"""
The Native XDoctest Runner
--------------------------

This file defines the native xdoctest interface to the collecting, executing,
and summarizing the results of running doctests. This is an alternative to
running through pytest.

Using the XDoctest Runner via the Terminal
------------------------------------------

This interface is exposed via the ``xdoctest.__main__`` script and can be
invoked on any module via: ``python -m xdoctest <modname>``, where
``<modname>`` is the path to. For example to run the tests in this module you
could execute:

.. code:: bash

    python -m xdoctest xdoctest.runner all

For more details see:

.. code:: bash

    python -m xdoctest --help

Using the XDoctest Runner Programmatically
------------------------------------------

This interface may also be run programmatically using
``xdoctest.doctest_module(path)``, which can be placed in the
``__main__`` section of any module as such:

.. code:: python

    if __name__ == '__main__':
        import xdoctest as xdoc
        xdoc.doctest_module(__file__)

This allows you to invoke the runner on a specific module by simply running
that module as the main module. Via: ``python -m <modname> <command>``. For
example, the this module ends with the previous code, which means you can
run the doctests as such:

.. code:: bash

    python -m xdoctest.runner list

"""
from xdoctest import dynamic_analysis
from xdoctest import core
from xdoctest import doctest_example
from xdoctest import utils
from functools import partial
import time
import types
import warnings
import sys
from xdoctest import global_state


def log(msg, verbose, level=1):
    """
    Simple conditional print logger

    Args:
        msg (str): message to print
        verbose (int): verbosity level, higher means more is print
        level (int): verbosity level at which this is printed. 0 is always,
            1 is info, 2 is verbose, 3 is very-verbose.
    """
    if verbose >= level:
        print(msg)


def doctest_callable(func):
    """
    Executes doctests an in-memory function or class.

    Args:
        func (callable):
            live method or class for which we will run its doctests.

    Example:
        >>> def inception(text):
        >>>     '''
        >>>     Example:
        >>>         >>> inception("I heard you liked doctests")
        >>>     '''
        >>>     print(text)
        >>> func = inception
        >>> doctest_callable(func)
    """
    from xdoctest.core import parse_docstr_examples
    doctests = list(parse_docstr_examples(
        func.__doc__, callname=func.__name__))
    # TODO: can this be hooked up into runner to get nice summaries?
    for doctest in doctests:

        # FIXME: each doctest needs a way of getting the globals of the scope
        # that the parent function was defined in.
        # HACK: to add module context, this might not be robust.
        doctest.module = sys.modules[func.__module__]
        doctest.global_namespace[func.__name__] = func
        doctest.run(verbose=3)


def gather_doctests(doctest_identifiers, style='auto', analysis='auto',
                    verbose=None):
    raise NotImplementedError('todo')


def doctest_module(module_identifier=None, command=None, argv=None, exclude=[],
                   style='auto', verbose=None, config=None, durations=None,
                   analysis='auto'):
    """
    Executes requestsed google-style doctests in a package or module.
    Main entry point into the testing framework.

    Args:
        module_identifier (str | ModuleType | None):
            The name of / path to the module, or the live module itself.
            If not specified, dynamic analysis will be used to introspect the
            module that called this function and that module will be used.
            This can also contain the callname followed by the ``::`` token.

        command (str):
            determines which doctests to run.
            if command is None, this is determined by parsing sys.argv
            Value values are
            'all' - find and run all tests in a module
            'list' - list the tests in a module
            'dump' - dumps tests to stdout

        argv (List[str] | None):
            if specified, command line flags that might influence beharior.
            if None uses sys.argv.
            SeeAlso :func:_update_argparse_cli
            SeeAlso :func:doctest_example.DoctestConfig._update_argparse_cli

        style (str): Determines how doctests are recognized and grouped.
            Can be freeform, google, or auto.

        verbose (int | None):
            Verbosity level.
            0 - disables all text
            1 - minimal printing
            3 - verbose printing

        exclude (List[str]):
            ignores any modname matching any of these glob-like patterns

        config (Dict[str, object]):
            modifies each examples configuration. Defaults and
            expected keys are documented in
            :class:`xdoctest.doctest_example.DoctestConfig`

        durations (int | None): if specified report top N slowest tests

        analysis (str): determines if doctests are found using static or
            dynamic analysis.

    Returns:
        Dict[str, Any]: run_summary

    Example:
        >>> modname = 'xdoctest.dynamic_analysis'
        >>> result = doctest_module(modname, 'list', argv=[''])

    Example:
        >>> # xdoctest: +SKIP
        >>> # Demonstrate different ways "module_identifier" can be specified
        >>> #
        >>> # Using a module name
        >>> result = doctest_module('xdoctest.static_analysis')
        >>> #
        >>> # Using a module path
        >>> result = doctest_module(os.expandpath('~/code/xdoctest/src/xdoctest/static_analysis.py'))
        >>> #
        >>> # Using a module itself
        >>> from xdoctest import runner
        >>> result = doctest_module(runner)
        >>> #
        >>> # Using a module name and a specific callname
        >>> from xdoctest import runner
        >>> result = doctest_module('xdoctest.static_analysis::parse_static_value')
    """
    _debug = partial(log, verbose=global_state.DEBUG_RUNNER)
    _debug('------+ DEBUG +------')
    _debug('CALLED doctest_module')
    _debug('exclude = {!r}'.format(exclude))
    _debug('argv = {!r}'.format(argv))
    _debug('command = {!r}'.format(command))
    _debug('module_identifier = {!r}'.format(module_identifier))
    _debug('durations = {!r}'.format(durations))
    _debug('config = {!r}'.format(config))
    _debug('verbose = {!r}'.format(verbose))
    _debug('style = {!r}'.format(style))
    _debug('------+ /DEBUG +------')

    modinfo = {
        'modpath': None,
        'modname': None,
        'module': None,
    }

    # TODO: allow a list of doctest specifiers to be passed.
    # TODO: abstract into a "gather" doctest method.
    if module_identifier is None:
        # Determine package name via caller if not specified
        frame_parent = dynamic_analysis.get_parent_frame()
        if '__file__' in frame_parent.f_globals:
            modinfo['modpath'] = frame_parent.f_globals['__file__']
        else:
            # Module might not exist as a path on disk, we might be trying to
            # test an IPython session.
            modinfo['modname'] = frame_parent.f_globals['__name__']
            modinfo['module'] = sys.modules[modinfo['modname']]
    else:
        if isinstance(module_identifier, types.ModuleType):
            modinfo['module'] = module_identifier
            modinfo['modpath'] = modinfo['module'].__file__
        else:
            # Allow the modname to contain the name of the test to be run
            if '::' in module_identifier:
                if command is None:
                    modpath_or_name, command = module_identifier.split('::')
                    modinfo['modpath'] = core._rectify_to_modpath(modpath_or_name)
                else:
                    raise ValueError('Command must be None if using :: syntax')
            else:
                modinfo['modpath'] = core._rectify_to_modpath(module_identifier)

    if config is None:
        config = doctest_example.DoctestConfig()

    command, style, verbose = _parse_commandline(command, style, verbose, argv)

    _log = partial(log, verbose=verbose)

    # Usually the "parseable_identifier" (i.e. the object we will extract the
    # docstrings from) is a path to a module, but sometimes we will only be
    # given the live module itself, hence the abstraction.
    if modinfo['modpath'] is None:
        parsable_identifier = modinfo['module']
    else:
        parsable_identifier = modinfo['modpath']

    _log('Start doctest_module({!r})'.format(parsable_identifier), level=2)
    _log('Listing tests', level=2)

    if command is None:
        # Display help if command is not specified
        _log('Not testname given. Use `all` to run everything or'
             ' pick from a list of valid choices:')
        command = 'list'

    # TODO: command should not be allowed to be the requested doctest name in
    # case it conflicts with an existing command. This probably requires an API
    # change to this function.
    gather_all = (command == 'all' or command == 'dump')

    tic = time.time()

    # Parse all valid examples
    with warnings.catch_warnings(record=True) as parse_warnlist:
        examples = list(core.parse_doctestables(
            parsable_identifier, exclude=exclude, style=style,
            analysis=analysis))
        # Set each example mode to native to signal that we are using the
        # native xdoctest runner instead of the pytest runner
        for example in examples:
            example.mode = 'native'

    if command == 'list':
        if len(examples) == 0:
            _log('... no docstrings with examples found')
        else:
            _log('    ' + '\n    '.join([example.cmdline  # + ' @ ' + str(example.lineno)
                                          for example in examples]))
        run_summary = {'action': 'list'}
    else:
        _log('gathering tests', level=2)
        enabled_examples = []
        for example in examples:
            if gather_all or command in example.valid_testnames:
                if gather_all and example.is_disabled():
                    continue
                enabled_examples.append(example)

        if len(enabled_examples) == 0:
            # Check for zero-arg funcs
            for example in _gather_zero_arg_examples(parsable_identifier):
                if command in example.valid_testnames:
                    enabled_examples.append(example)

                elif command in ['zero-all', 'zero', 'zero_all', 'zero-args']:
                    enabled_examples.append(example)

        if config:
            for example in enabled_examples:
                example.config.update(config)

        if command == 'dump':
            # format the doctests as normal unit tests
            _log('dumping tests to stdout', level=2)
            module_text = _convert_to_test_module(enabled_examples)
            _log(module_text, level=0)

            run_summary = {'action': 'dump'}
        else:
            # Run the gathered doctest examples

            RANDOMIZE_ORDER = False
            if RANDOMIZE_ORDER:
                # randomize the order in which tests are run
                import random
                random.shuffle(enabled_examples)

            run_summary = _run_examples(enabled_examples, verbose, config,
                                        _log=_log)

            toc = time.time()
            n_seconds = toc - tic

            #### TODO: callback and plugin system.
            # Can probably reuse some other library for this.

            # Print final summary info in a style similar to pytest
            if verbose >= 0 and run_summary:
                _print_summary_report(run_summary, parse_warnlist, n_seconds,
                                      enabled_examples, durations,
                                      config=config, _log=_log)

            # Hidden experimental feature
            import os
            insert_skip_directive_above_failures = (
                os.environ.get('XDOCTEST_INSERT_SKIP_DIRECTIVE_ABOVE_FAILURES') or
                '--insert-skip-directive-above-failures' in sys.argv
            )
            AFTER_ALL_HOOKS = []
            if insert_skip_directive_above_failures:
                AFTER_ALL_HOOKS.append(_auto_disable_failing_tests_hook)
            for hook in AFTER_ALL_HOOKS:
                context = {
                    'enabled_example': enabled_examples,
                    'run_summary': run_summary,
                }
                hook(context)

    return run_summary


def _auto_disable_failing_tests_hook(context):
    """
    Experimental feature to modify code based on failing tests.
    This should likely be moved to its own submodule.
    """
    from collections import defaultdict
    run_summary = context['run_summary']
    failing_examples = run_summary['failed']
    path_to_failed_linos = defaultdict(list)
    for example in failing_examples:
        # We could disable at the point of failure, or at the start of the
        # test. While I'm tempted to use the failing one, as it makes it more
        # clear what to fix, that introduces potential incompatibility with
        # got/want style errors, so let's default to the first line.
        WHERE_INSERT = 'start-of-doctest'
        failed_line_number = example.failed_lineno()
        start_line_number = example.lineno
        if WHERE_INSERT == 'start-of-doctest':
            insert_line_number = start_line_number
        elif WHERE_INSERT == 'failing-location':
            insert_line_number = failed_line_number
        path_to_failed_linos[example.fpath].append(insert_line_number)

    for fpath, skip_linenos in path_to_failed_linos.items():
        print('modifying fpath={}'.format(fpath))
        with open(fpath, 'r') as file:
            lines = file.readlines()
        # Insert the lines in reverse order
        for lineno in sorted(skip_linenos)[::-1]:
            line_idx = lineno - 1
            failed_line = lines[line_idx]
            num_indent_chars = len(failed_line) - len(failed_line.lstrip())
            indent = failed_line[:num_indent_chars]
            endl = '\n'  # is there a case we use a different line end?
            new_line = ''.join([indent, '>>> # xdoctest: +SKIP', endl])
            # Dont insert the same line twice, its failing for some other reason
            # Probably a pre-import
            if failed_line != new_line:
                lines.insert(line_idx, new_line)
        with open(fpath, 'w') as file:
            file.write(''.join(lines))


def _convert_to_test_module(enabled_examples):
    """
    Logic for the "dumps" command.

    Converts all doctests to unit tests that can exist in a standalone module
    """
    dump_config = {
        'remove_import_star': True,
    }
    # from xdoctest import static_analysis as static

    module_lines = []
    for example in enabled_examples:

        # Create a unit-testable function for this example
        func_name = 'test_' + example.modname.replace('.', '_') + '_' + example.callname.replace('.', '_')
        body_lines = []

        docstr_lines = [
            '"""',
            'converted from {}'.format(example.node),
            '"""',
        ]
        header_lines = []

        if example.config['global_exec'] is not None:
            # It might also be a reasonable idea to put the global exec at the
            # top, but this is more accurate to how it actually runs.
            # hack for newlines, not sure why it is escaping them.
            global_lines = example.config['global_exec'].split('\\n')
            header_lines.extend([g + '  # NOQA' for g in global_lines])

        for part in example._parts:

            if dump_config['remove_import_star']:
                new_exec_lines = []
                for line in part.exec_lines:
                    # TODO: this is not robust, need AST magic here
                    # import ubelt as ub
                    # print('line = {}'.format(ub.repr2(line, nl=1)))
                    # stripped = static._strip_hashtag_comments_and_newlines(line)
                    if ' import *' in line:
                        continue
                    new_exec_lines.append(line)
                part.exec_lines = new_exec_lines

            body_part = part.format_part(linenos=False, want=False,
                                         prefix=False, colored=False,
                                         partnos=False)
            if part.want:
                want_text = '# doctest want:\n'
                want_text += utils.indent(part.want, '# ')
                body_part += '\n' + want_text
            body_lines.append(body_part)
        if len(body_lines) == 0:
            body_lines.append('...')

        body = '\n'.join(docstr_lines + header_lines + body_lines)

        try:
            undefined = sorted(undefined_names(body))
            if undefined:
                # Assume we can find them in the parent module
                header_lines.append('from {} import {}'.format(example.modname, ', '.join(undefined)))
                body = '\n'.join(docstr_lines + header_lines + body_lines)
        except Exception:
            warnings.warn('Unable to check for undefined names without pyflakes')

        # if '+SKIP' in body:
        #     continue
        # if '+REQUIRES' in body:
        #     continue
        func_text = 'def {}():\n'.format(func_name) + utils.indent(body)
        module_lines.append(func_text)

    module_text = '\n\n\n'.join(module_lines)
    return module_text


def undefined_names(sourcecode):
    """
    Parses source code for undefined names

    Args:
        sourcecode (str): code to check for unused names

    Returns:
        Set[str]: the unused variable names

    Example:
        >>> # xdoctest: +REQUIRES(module:pyflakes)
        >>> print(undefined_names('x = y'))
        {'y'}
    """
    import pyflakes.api
    import pyflakes.reporter

    class CaptureReporter(pyflakes.reporter.Reporter):
        def __init__(reporter, warningStream, errorStream):
            reporter.syntax_errors = []
            reporter.messages = []
            reporter.unexpected = []

        def unexpectedError(reporter, filename, msg):
            reporter.unexpected.append(msg)

        def syntaxError(reporter, filename, msg, lineno, offset, text):
            reporter.syntax_errors.append(msg)

        def flake(reporter, message):
            reporter.messages.append(message)

    names = set()

    reporter = CaptureReporter(None, None)
    pyflakes.api.check(sourcecode, '_.py', reporter)
    for msg in reporter.messages:
        if msg.__class__.__name__.endswith('UndefinedName'):
            assert len(msg.message_args) == 1
            names.add(msg.message_args[0])
    return names


def _print_summary_report(run_summary, parse_warnlist, n_seconds,
                          enabled_examples, durations, config=None, _log=None):
    """
    Summary report formatting and printing
    """
    def cprint(text, color):
        if config is not None and config.get('colored', True):
            _log(utils.color_text(text, color))
        else:
            _log(text)

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
            _log(utils.indent(
                warnings.formatwarning(warn.message, warn.category,
                                       warn.filename, warn.lineno)))

    # report run-time warnings
    if warned:
        cprint('\n=== Found {} run-time warnings ==='.format(len(warned)), 'yellow')
        for warn_idx, example in enumerate(warned, start=1):
            cprint('--- Runtime Warning: {} / {} ---'.format(warn_idx, len(warned)),
                   'yellow')
            _log('example = {!r}'.format(example))
            for warn in example.warn_list:
                _log(utils.indent(
                    warnings.formatwarning(warn.message, warn.category,
                                           warn.filename, warn.lineno)))

    if failed and len(enabled_examples) > 1:
        # If there is more than one test being run, _log out all the
        # errors that occurred so they are consolidated in a single place.
        cprint('\n=== Found {} errors ==='.format(len(failed)), 'red')
        for fail_idx, example in enumerate(failed, start=1):
            cprint('--- Error: {} / {} ---'.format(fail_idx, len(failed)), 'red')
            _log(utils.indent('\n'.join(example.repr_failure())))

    # Print command lines to re-run failed tests
    if failed:
        cprint('\n=== Failed tests ===', 'red')
        for example in failed:
            _log(example.cmdline)

    # final summary
    n_passed = run_summary.get('n_passed', 0)
    n_failed = run_summary.get('n_failed', 0)
    n_skipped = run_summary.get('n_skipped', 0)
    n_warnings = len(warned) + len(parse_warnlist)
    pairs = zip([n_failed, n_passed, n_skipped, n_warnings],
                ['failed', 'passed', 'skipped', 'warnings'])
    parts = ['{n} {t}'.format(n=n, t=t) for n, t in pairs  if n > 0]
    _fmtstr = '=== ' + ', '.join(parts) + ' in {n_seconds:.2f} seconds ==='
    # _fmtstr = '=== ' + ' '.join(parts) + ' in {n_seconds:.2f} seconds ==='
    summary_line = _fmtstr.format(n_seconds=n_seconds)
    # color text based on worst type of error
    if n_failed > 0:
        cprint(summary_line, 'red')
    elif n_warnings > 0 or (n_passed == 0 and n_skipped > 0):
        cprint(summary_line, 'yellow')
    else:
        cprint(summary_line, 'green')

    if durations is not None:
        times = run_summary.get('times', {})
        test_time_tups = sorted(times.items(), key=lambda x: x[1])
        if durations > 0:
            test_time_tups = test_time_tups[-durations:]
        for example, n_secs in test_time_tups:
            _log('time: {:0.8f}, test: {}'.format(n_secs, example.cmdline))


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


def _run_examples(enabled_examples, verbose, config=None, _log=None):
    """
    Internal helper, loops over each example, runs it, returns a summary
    """
    n_total = len(enabled_examples)
    _log('running %d test(s)' % n_total)
    summaries = []
    failed = []
    warned = []
    times = {}
    # It is important to raise immediately within the test to display errors
    # returned from multiprocessing. Especially in zero-arg mode

    on_error = 'return' if n_total > 1 else 'raise'
    on_error = 'return'

    for example in enabled_examples:
        try:
            try:
                tic = time.time()
                summary = example.run(verbose=verbose, on_error=on_error)
                toc = time.time()
                n_seconds = toc - tic
                times[example] = n_seconds
            except Exception:
                _log('\n'.join(example.repr_failure(with_tb=False)))
                raise

            summaries.append(summary)
            if example.warn_list:
                warned.append(example)
            if summary['skipped']:
                pass
                # if verbose == 0:
                #     # TODO: should we write anything when verbose=0?
                #     sys.stdout.write('S')
                #     sys.stdout.flush()
            elif summary['passed']:
                pass
                # if verbose == 0:
                #     # TODO: should we write anything when verbose=0?
                #     sys.stdout.write('.')
                #     sys.stdout.flush()
            else:
                failed.append(example)
                # if verbose == 0:
                #     sys.stdout.write('F')
                #     sys.stdout.flush()
                if on_error == 'raise':
                    # What happens if we don't re-raise here?
                    # If it is necessary, write a message explaining why
                    _log('\n'.join(example.repr_failure()))
                    ex_value = example.exc_info[1]
                    raise ex_value
        except KeyboardInterrupt:
            _log('Caught CTRL+c: Stopping tests')
            break
        # except Exception:
        #     summary = {'passed': False}
        #     if verbose == 0:
        #         sys.stdout.write('F')
        #         sys.stdout.flush()
    if verbose == 0:
        _log('')
    n_passed = sum(s['passed'] for s in summaries)
    n_failed = sum(s['failed'] for s in summaries)
    n_skipped = sum(s['skipped'] for s in summaries)

    if config is not None and config.get('colored', True):
        _log(utils.color_text('============', 'white'))
    else:
        _log('============')

    if n_total > 1:
        # and verbose > 0:
        _log('Finished doctests')
        _log('%d / %d passed'  % (n_passed, n_total))

    run_summary = {
        'failed': failed,
        'warned': warned,
        'action': 'run_examples',
        'n_warned': len(warned),
        'n_skipped': n_skipped,
        'n_passed': n_passed,
        'n_failed': n_failed,
        'n_total': n_total,
        'times': times,
    }
    return run_summary


def _parse_commandline(command=None, style='auto', verbose=None, argv=None):
    # Determine command via sys.argv if not specified
    doctest_example.DoctestConfig()

    if argv is None:
        argv = sys.argv[1:]

    if command is None:
        if len(argv) >= 1:
            if argv[0] and not argv[0].startswith('-'):
                command = argv[0]

    # Change how docstrs are found
    # TODO: Undocumented flags. Either document in argparse or remove.
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


def _update_argparse_cli(add_argument, prefix=None):
    """
    Update the CLI with arguments that control how doctests are collected ando
    how aggregate results are reported.
    """
    import os
    add_argument(*('-m', '--modname'), type=str,
                 help='Module name or path. If specified positional modules are ignored',
                 default=None)

    add_argument(*('-c', '--command'), type=str,
                 help=(
                     'A doctest name or a command (all|list|dump|<callname>). '
                     'Defaults to `all` (which runs everything). Using `list` will '
                     'collect and print all doctests. '
                     'Using `dump` will convert doctests into unit tests. '
                     'Anything else will be interpreted as a "callname"'),
                 default=None)

    add_argument(*('--style',), type=str,
                 help='Choose the style of doctests that will be parsed',
                 choices=['auto', 'google', 'freeform'],
                 default=os.environ.get('XDOCTEST_STYLE', 'auto'))

    add_argument(*('--analysis',), type=str,
                 help='How doctests are collected',
                 choices=['auto', 'static', 'dynamic'],
                 default=os.environ.get('XDOCTEST_ANALYSIS', 'auto'))

    add_argument(*('--durations',), type=int,
                 help=('Specify execution times for slowest N tests.'
                       'N=0 will show times for all tests'),
                 default=None)

    add_argument(*('--time',), dest='time', action='store_true',
                 help=('Same as if durations=0'))

    add_argument_kws = [
        # (['--style'], dict(dest='style',
        #                    type=str, help='choose your style',
        #                    choices=['auto', 'google', 'freeform'], default='auto')),
        # (['--quiet'], dict(type=int, action='store_false', dest='verbose',
        #                          help='sets verbosity=0')),
    ]

    if prefix is None:
        prefix = ['']

    environ_aware = {'style', 'analysis'}
    for alias, kw in add_argument_kws:
        # Use environment variables for some defaults
        argname = alias[0].lstrip('-')
        if argname in environ_aware:
            env_argname = 'XDOCTEST_' + argname.replace('-', '_').upper()
            if 'default' in kw:
                kw['default'] = os.environ.get(env_argname, kw['default'])
        alias = [
            a.replace('--', '--' + p + '-') if p else a
            for a in alias for p in prefix
        ]
        if prefix[0]:
            kw['dest'] = prefix[0] + '_' + kw['dest']
        add_argument(*alias, **kw)


if __name__ == '__main__':
    r"""
    CommandLine:
        python -m xdoctest.runner all
    """
    import xdoctest as xdoc
    xdoc.doctest_module()

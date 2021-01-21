# -*- coding: utf-8 -*-
"""
This module defines the main class that holds a DocTest example
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import __future__
from collections import OrderedDict
import traceback
import six
import warnings
import math
import sys
import re
from xdoctest import utils
from xdoctest import directive
from xdoctest import constants
from xdoctest import static_analysis as static
from xdoctest import parser
from xdoctest import checker
from xdoctest import exceptions

# I believe the original reason for this hack was fixed in 3.9rc (The CI will
# tell us otherwise if this is incorrect)
# from distutils.version import LooseVersion
# EVAL_MIGHT_RETURN_COROUTINE = LooseVersion(sys.version.split(' ')[0]) >= LooseVersion('3.9.0')
# EVAL_MIGHT_RETURN_COROUTINE = False

__devnotes__ = """
TODO:
    - [ ] Rename DocTest to Doctest?
"""


class DoctestConfig(dict):
    """
    Doctest configuration

    Static configuration for collection, execution, and reporting doctests.
    Note dynamic directives are not managed by DoctestConfig, they use
    RuntimeState.
    """
    def __init__(self, *args, **kwargs):
        super(DoctestConfig, self).__init__(*args, **kwargs)
        self.update({
            # main options exposed by command line runner/plugin
            'colored': hasattr(sys.stdout, 'isatty') and sys.stdout.isatty(),
            'reportchoice': 'udiff',
            'default_runtime_state': {},
            'offset_linenos': False,
            'global_exec': None,
            'on_error': 'raise',
            'partnos': False,
            'verbose': 1,
        })

    def _populate_from_cli(self, ns):
        from xdoctest.directive import parse_directive_optstr
        directive_optstr = ns['options']
        default_runtime_state = {}
        if directive_optstr:
            for optpart in directive_optstr.split(','):
                directive = parse_directive_optstr(optpart)
                default_runtime_state[directive.name] = directive.positive
        _examp_conf = {
            'default_runtime_state': default_runtime_state,
            'offset_linenos': ns['offset_linenos'],
            'colored': ns['colored'],
            'reportchoice': ns['reportchoice'],
            'global_exec': ns['global_exec'],
            'verbose': ns['verbose'],
        }
        return _examp_conf

    def _update_argparse_cli(self, add_argument, prefix=None, defaults={}):
        """
        Updates a pytest or argparse CLI

        Args:
            add_argument (callable): the parser.add_argument function
        """
        import argparse
        def str_lower(x):
            # python2 fix
            return str.lower(str(x))

        add_argument_kws = [
            (['--colored'], dict(dest='colored', default=self['colored'],
                                 help=('Enable or disable ANSI coloration in stdout'))),
            (['--nocolor'], dict(dest='colored', action='store_false',
                                 default=argparse.SUPPRESS,
                                 help=('Disable ANSI coloration in stdout'))),
            (['--offset'], dict(dest='offset_linenos', action='store_true',
                                default=self['offset_linenos'],
                                help=('if True formatted source linenumbers will agree with '
                                      'their location in the source file. Otherwise they '
                                      'will be relative to the doctest itself.'))),
            (['--report'], dict(dest='reportchoice',
                                type=str_lower,
                                choices=('none', 'cdiff', 'ndiff', 'udiff', 'only_first_failure',),
                                default=self['reportchoice'],
                                help=('choose another output format for diffs on xdoctest failure'))),
            # used to build default_runtime_state
            (['--options'], dict(type=str_lower, default=None, dest='options',
                                 help='default directive flags for doctests')),
            (['--global-exec'], dict(type=str, default=None, dest='global_exec',
                                     help='exec these lines before every test')),
            (['--verbose'], dict(type=int, default=defaults.get('verbose', 3), dest='verbose',
                                     help='verbosity level')),
            # (['--verbose'], dict(action='store_true', dest='verbose')),
            (['--quiet'], dict(action='store_true', dest='verbose',
                                default=argparse.SUPPRESS,
                                help='sets verbosity to 1')),
            (['--silent'], dict(action='store_false', dest='verbose',
                                default=argparse.SUPPRESS,
                                help='sets verbosity to 0')),
        ]

        if prefix is None:
            prefix = ['']

        for alias, kw in add_argument_kws:
            alias = [
                a.replace('--', '--' + p + '-') if p else a
                for a in alias for p in prefix
            ]
            if prefix[0]:
                kw['dest'] = prefix[0] + '_' + kw['dest']
            add_argument(*alias, **kw)

    def getvalue(self, key, given=None):
        if given is None:
            return self[key]
        else:
            return given


class DocTest(object):
    """
    Holds information necessary to execute and verify a doctest

    Attributes:

        docsrc (str):
            doctest source code

        modpath (str | PathLike, default=None):
            module the source was read from

        callname (str, default=None):
            name of the function/method/class/module being tested

        num (int, default=0):
            the index of the doctest in the docstring. (i.e. this object
            refers to the num-th doctest within a docstring)

        lineno (int, default=1):
            The line (starting from 1) in the file that the doctest begins on.
            (i.e. if you were to go to this line in the file, the first line of
            the doctest should be on this line).

        fpath (PathLike):
            Typically the same as modpath, only specified for non-python files
            (e.g. rst files).

        block_type (str, default=None):
            Hint indicating the type of docstring block. Can be ('Example',
            'Doctest', 'Script', 'Benchmark', 'zero-arg', etc..).

        mode (str, default='pytest'):
            Hint at what created / is running this doctest. This impacts
            how results are presented and what doctests are skipped.

    CommandLine:
        xdoctest -m xdoctest.doctest_example DocTest

    Example:
        >>> from xdoctest import core
        >>> from xdoctest import doctest_example
        >>> import os
        >>> modpath = doctest_example.__file__.replace('.pyc', '.py')
        >>> modpath = os.path.realpath(modpath)
        >>> testables = core.parse_doctestables(modpath)
        >>> for test in testables:
        >>>     if test.callname == 'DocTest':
        >>>         self = test
        >>>         break
        >>> assert self.num == 0
        >>> assert self.modpath == modpath
        >>> print(self)
        <DocTest(xdoctest.doctest_example DocTest:0 ln ...)>
    """

    # Constant values for unknown attributes
    UNKNOWN_MODNAME = '<modname?>'
    UNKNOWN_MODPATH = '<modpath?>'
    UNKNOWN_CALLNAME = '<callname?>'
    UNKNOWN_FPATH = '<fpath?>'

    def __init__(self, docsrc, modpath=None, callname=None, num=0,
                 lineno=1, fpath=None, block_type=None, mode='pytest'):
        import types
        # if we know the google block type it is recorded
        self.block_type = block_type

        self.config = DoctestConfig()

        self.module = None
        self.modpath = modpath

        self.fpath = fpath
        if modpath is None:
            self.modname = self.UNKNOWN_MODNAME
            self.modpath = self.UNKNOWN_MODPATH
        elif isinstance(modpath, types.ModuleType):
            self.fpath = modpath
            self.module = modpath
            self.modname = modpath.__name__
            self.modpath = getattr(self.module, '__file__', self.UNKNOWN_MODPATH)
        else:
            if fpath is not None:
                if fpath != modpath:
                    raise AssertionError(
                        'only specify fpath for non-python files')
            self.fpath = modpath
            self.modname = static.modpath_to_modname(modpath)
        if callname is None:
            self.callname = self.UNKNOWN_CALLNAME
        else:
            self.callname = callname
        self.docsrc = docsrc
        self.lineno = lineno

        self.num = num

        self._parts = None
        self.failed_tb_lineno = None
        self.exc_info = None
        self.failed_part = None
        self.warn_list = None

        self.logged_evals = OrderedDict()
        self.logged_stdout = OrderedDict()
        self._unmatched_stdout = []
        self._skipped_parts = []

        self._runstate = None

        # Maintain global variables that this test will have access to
        self.global_namespace = {}
        # Hint at what is running this doctest
        self.mode = mode

    def __nice__(self):
        parts = []
        parts.append(self.modname)
        parts.append('%s:%s' % (self.callname, self.num))
        if self.lineno is not None:
            parts.append('ln %s' % (self.lineno))
        return ' '.join(parts)

    def __repr__(self):
        classname = self.__class__.__name__
        devnice = self.__nice__()
        return '<%s(%s) at %s>' % (classname, devnice, hex(id(self)))

    def __str__(self):
        classname = self.__class__.__name__
        devnice = self.__nice__()
        return '<%s(%s)>' % (classname, devnice)

    def is_disabled(self, pytest=False):
        """
        Checks for comment directives on the first line of the doctest

        A doctest is disabled if it starts with any of the following patterns:
            # DISABLE_DOCTEST
            # SCRIPT
            # UNSTABLE
            # FAILING

        And if running in pytest, you can also use
            # pytest.skip
        """
        disable_patterns = [
            r'>>>\s*#\s*DISABLE',
            r'>>>\s*#\s*UNSTABLE',
            r'>>>\s*#\s*FAILING',
            r'>>>\s*#\s*SCRIPT',
            r'>>>\s*#\s*SLOW_DOCTEST',
            # r'>>>\s*#\s*x?doctest:\s\+SKIP',
        ]
        if pytest:
            disable_patterns += [
                r'>>>\s*#\s*pytest.skip'
            ]

        pattern = '|'.join(disable_patterns)
        m = re.match(pattern, self.docsrc, flags=re.IGNORECASE)
        return m is not None

    @property
    def unique_callname(self):
        return self.callname + ':' + str(self.num)

    @property
    def node(self):
        """ this pytest node """
        return self.modpath + '::' + self.callname + ':' + str(self.num)

    @property
    def valid_testnames(self):
        return {
            self.callname,
            self.unique_callname,
        }

    def wants(self):
        """
        Returns a list of the populated wants
        """
        self._parse()
        for part in self._parts:
            if part.want:
                yield part.want

    def format_parts(self, linenos=True, colored=None, want=True,
                     offset_linenos=None, prefix=True):
        """ used by format_src """
        self._parse()
        colored = self.config.getvalue('colored', colored)
        partnos = self.config.getvalue('partnos')
        offset_linenos = self.config.getvalue('offset_linenos', offset_linenos)

        n_digits = None
        startline = 1
        if linenos:
            if offset_linenos:
                startline = self.lineno
            n_lines = sum(p.n_lines for p in self._parts)
            endline = startline + n_lines

            n_digits = math.log(max(1, endline), 10)
            n_digits = int(math.ceil(n_digits))

        for part in self._parts:
            part_text = part.format_part(linenos=linenos, want=want,
                                         startline=startline,
                                         n_digits=n_digits, prefix=prefix,
                                         colored=colored, partnos=partnos)
            yield part_text

    def format_src(self, linenos=True, colored=None, want=True,
                   offset_linenos=None, prefix=True):
        """
        Adds prefix and line numbers to a doctest

        Args:
            linenos (bool): if True, adds line numbers to output

            colored (bool): if True highlight text with ansi colors. Default
                is specified in the config.

            want (bool): if True includes "want" lines (default False).

            offset_linenos (bool): if True offset line numbers to agree with
                their position in the source text file (default False).

            prefix (bool): if False, exclude the doctest `>>> ` prefix

        Example:
            >>> from xdoctest.core import *
            >>> from xdoctest import core
            >>> testables = parse_doctestables(core.__file__)
            >>> self = next(testables)
            >>> self._parse()
            >>> print(self.format_src())
            >>> print(self.format_src(linenos=False, colored=False))
            >>> assert not self.is_disabled()
        """
        formated_parts = list(self.format_parts(linenos=linenos,
                                                colored=colored, want=want,
                                                offset_linenos=offset_linenos,
                                                prefix=prefix))
        full_source = '\n'.join(formated_parts)
        return full_source

    def _parse(self):
        """
        Divide the given string into examples and intervening text.

        Example:
            >>> s = 'I am a dummy example with three parts'
            >>> x = 10
            >>> print(s)
            I am a dummy example with three parts
            >>> s = 'My purpose it so demonstrate how wants work here'
            >>> print('The new want applies ONLY to stdout')
            >>> print('given before the last want')
            >>> '''
                this wont hurt the test at all
                even though its multiline '''
            >>> y = 20
            The new want applies ONLY to stdout
            given before the last want
            >>> # Parts from previous examples are executed in the same context
            >>> print(x + y)
            30

            this is simply text, and doesnt apply to the previous doctest the
            <BLANKLINE> directive is still in effect.

        Example:
            >>> from xdoctest import parser
            >>> from xdoctest.docstr import docscrape_google
            >>> from xdoctest import doctest_example
            >>> DocTest = doctest_example.DocTest
            >>> docstr = DocTest._parse.__doc__
            >>> blocks = docscrape_google.split_google_docblocks(docstr)
            >>> doclineno = DocTest._parse.__code__.co_firstlineno
            >>> key, (docsrc, offset) = blocks[-2]
            >>> lineno = doclineno + offset
            >>> self = DocTest(docsrc, doctest_example.__file__, '_parse', 0,
            >>>                lineno)
            >>> self._parse()
            >>> assert len(self._parts) >= 3
            >>> #p1, p2, p3 = self._parts
            >>> self.run()
        """
        if not self._parts:
            info = dict(callname=self.callname, modpath=self.modpath,
                        lineno=self.lineno, fpath=self.fpath)
            self._parts = parser.DoctestParser().parse(self.docsrc, info)
            self._parts = [p for p in self._parts
                           if not isinstance(p, six.string_types)]
        # Ensure part numbers are given
        for partno, part in enumerate(self._parts):
            part.partno = partno

    def _import_module(self):
        """
        After this point we are in dynamic analysis mode, in most cases
        xdoctest should have been in static-analysis-only mode.
        """
        if self.module is None:
            if not self.modname.startswith('<'):
                # self.module = utils.import_module_from_path(self.modpath, index=0)
                self.module = utils.import_module_from_path(self.modpath, index=-1)

    @staticmethod
    def _extract_future_flags(namespace):
        """
        Return the compiler-flags associated with the future features that
        have been imported into the given namespace (i.e. globals).
        """
        compileflags = 0
        for key in __future__.all_feature_names:
            feature = namespace.get(key, None)
            if feature is getattr(__future__, key):
                compileflags |= feature.compiler_flag
        return compileflags

    def _test_globals(self):
        test_globals = self.global_namespace
        if self.module is None:
            compileflags = 0
        else:
            test_globals.update(self.module.__dict__)
            compileflags = self._extract_future_flags(test_globals)
        # force print function and division futures
        compileflags |= __future__.print_function.compiler_flag
        compileflags |= __future__.division.compiler_flag
        return test_globals, compileflags

    def anything_ran(self):
        # If everything was skipped, then there will be no stdout
        return len(self.logged_stdout) > 0

    def run(self, verbose=None, on_error=None):
        """
        Executes the doctest, checks the results, reports the outcome.

        Args:
            verbose (int): verbosity level
            on_error (str): can be 'raise' or 'return'

        Returns:
            Dict : summary
        """
        on_error = self.config.getvalue('on_error', on_error)
        verbose = self.config.getvalue('verbose', verbose)
        if on_error not in {'raise', 'return'}:
            raise KeyError(on_error)

        self._parse()  # parse out parts if we have not already done so
        self._pre_run(verbose)
        self._import_module()

        # Prepare for actual test run
        test_globals, compileflags = self._test_globals()

        self.logged_evals.clear()
        self.logged_stdout.clear()
        self._unmatched_stdout = []

        self._skipped_parts = []
        self.exc_info = None
        self._suppressed_stdout = verbose <= 1

        # Initialize a new runtime state
        default_state = self.config['default_runtime_state']
        runstate = self._runstate = directive.RuntimeState(default_state)
        # setup reporting choice
        runstate.set_report_style(self.config['reportchoice'].lower())

        global_exec = self.config.getvalue('global_exec')
        if global_exec:
            # Hack to make it easier to specify multi-line input on the CLI
            global_source = utils.codeblock(global_exec.replace('\\n', '\n'))
            global_code = compile(
                global_source, mode='exec',
                filename='<doctest:' + self.node + ':' + 'global_exec>',
                flags=compileflags, dont_inherit=True
            )
            exec(global_code, test_globals)

        # Can't do this because we can't force execution of SCRIPTS
        # if self.is_disabled():
        #     runstate['SKIP'] = True

        # - [x] TODO: fix CaptureStdout so it doesn't break embedding shells
        # don't capture stdout for zero-arg blocks
        # needs_capture = self.block_type != 'zero-arg'
        # I think the bug that broke embedding shells is fixed, so it is now
        # safe to capture. If not, uncomment above lines. If this works without
        # issue, then remove these notes in a future version.
        # needs_capture = False
        needs_capture = True

        # Use the same capture object for all parts in the test
        cap = utils.CaptureStdout(supress=self._suppressed_stdout,
                                  enabled=needs_capture)
        with warnings.catch_warnings(record=True) as self.warn_list:
            for partx, part in enumerate(self._parts):
                # Extract directives and and update runtime state
                runstate.update(part.directives)

                # Handle runtime actions
                if runstate['SKIP'] or len(runstate['REQUIRES']) > 0:
                    self._skipped_parts.append(part)
                    continue

                # Prepare to capture stdout and evaluated values
                self.failed_part = part
                got_eval = constants.NOT_EVALED
                try:
                    # Compile code, handle syntax errors
                    #   part.compile_mode can be single, exec, or eval.
                    #   Typically single is used instead of eval
                    self._partfilename = '<doctest:' + self.node + '>'
                    code = compile(
                        part.source, mode=part.compile_mode,
                        filename=self._partfilename,
                        flags=compileflags, dont_inherit=True
                    )
                except KeyboardInterrupt:  # nocover
                    raise
                except Exception:
                    raise
                    # self.exc_info = sys.exc_info()
                    # ex_type, ex_value, tb = self.exc_info
                    # self.failed_tb_lineno = tb.tb_lineno
                    # if on_error == 'raise':
                    #     raise
                try:
                    # Execute the doctest code
                    try:
                        # NOTE: For code passed to eval or exec, there is no
                        # difference between locals and globals. Only pass in
                        # one dict, otherwise there is weird behavior
                        with cap:
                            # We can execute each part using exec or eval.  If
                            # a doctest part has `compile_mode=eval` we
                            # exepect it to return an object with a repr that
                            # can compared to a "want" statement.
                            # print('part.compile_mode = {!r}'.format(part.compile_mode))
                            if part.compile_mode == 'eval':
                                # print('test_globals = {}'.format(sorted(test_globals.keys())))
                                got_eval = eval(code, test_globals)
                                # if EVAL_MIGHT_RETURN_COROUTINE:
                                #     import types
                                #     if isinstance(got_eval, types.CoroutineType):
                                #         # In 3.9-rc (2020-mar-31) it looks like
                                #         # eval sometimes returns coroutines. I
                                #         # found no docs on this. Not sure if it
                                #         # will be mainlined, but this seems to
                                #         # fix it.
                                #         import asyncio
                                #         got_eval =  asyncio.run(got_eval)
                            else:
                                exec(code, test_globals)

                        # Record any standard output and "got_eval" produced by
                        # this doctest_part.
                        self.logged_evals[partx] = got_eval
                        self.logged_stdout[partx] = cap.text
                    except Exception:
                        if part.want:
                            # A failure may be expected if the traceback
                            # matches the part's want statement.
                            exception = sys.exc_info()
                            traceback.format_exception_only(*exception[:2])
                            exc_got = traceback.format_exception_only(*exception[:2])[-1]
                            want = part.want
                            checker.check_exception(exc_got, want, runstate)
                        else:
                            raise
                    else:
                        """
                        TODO:
                            [ ] - Delay got-want failure until the end of the
                            doctest. Allow the rest of the code to run.  If
                            multiple errors occur, show them both.
                        """
                        if part.want:
                            got_stdout = cap.text
                            if not runstate['IGNORE_WANT']:
                                part.check(got_stdout, got_eval, runstate,
                                           unmatched=self._unmatched_stdout)
                            # Clear unmatched output when a check passes
                            self._unmatched_stdout = []
                        else:
                            # If a part doesnt have a want allow its output to
                            # be matched by the next part.
                            self._unmatched_stdout.append(cap.text)

                # Handle anything that could go wrong
                except KeyboardInterrupt:  # nocover
                    raise
                except (exceptions.ExitTestException,
                        exceptions._pytest.outcomes.Skipped):
                    if verbose > 0:
                        print('Test gracefully exists')
                    break
                except checker.GotWantException:
                    # When the "got", does't match the "want"
                    self.exc_info = sys.exc_info()
                    if on_error == 'raise':
                        raise
                    break
                except checker.ExtractGotReprException as ex:
                    # When we fail to extract the "got"
                    self.exc_info = sys.exc_info()
                    if on_error == 'raise':
                        raise ex.orig_ex
                    break
                except Exception as _ex_dbg:
                    ex_type, ex_value, tb = sys.exc_info()

                    DEBUG = 0
                    if DEBUG:
                        print('_ex_dbg = {!r}'.format(_ex_dbg))
                        print('<DEBUG: doctest encountered exception>', file=sys.stderr)
                        print(''.join(traceback.format_tb(tb)), file=sys.stderr)
                        print('</DEBUG>', file=sys.stderr)

                    # Search for the traceback that corresponds with the
                    # doctest, and remove the parts that point to
                    # boilerplate lines in this file.
                    found_lineno = None
                    for sub_tb in _traverse_traceback(tb):
                        tb_filename = sub_tb.tb_frame.f_code.co_filename
                        if tb_filename == self._partfilename:
                            # Walk up the traceback until we find the one that has
                            # the doctest as the base filename
                            found_lineno = sub_tb.tb_lineno
                            break
                    if DEBUG:
                        # The only traceback remaining should be
                        # the part that is relevant to the user
                        print('<DEBUG: best sub_tb>', file=sys.stderr)
                        print('found_lineno = {!r}'.format(found_lineno), file=sys.stderr)
                        print(''.join(traceback.format_tb(sub_tb)), file=sys.stderr)
                        print('</DEBUG>', file=sys.stderr)

                    if found_lineno is None:
                        if DEBUG:
                            print('UNABLE TO CLEAN TRACEBACK. EXIT DUE TO DEBUG')
                            sys.exit(1)
                        raise ValueError('Could not clean traceback: ex = {!r}'.format(_ex_dbg))
                    else:
                        self.failed_tb_lineno = found_lineno

                    self.exc_info = (ex_type, ex_value, tb)

                    # The idea of CLEAN_TRACEBACK is to make it so the
                    # traceback from this function doesn't clutter the error
                    # message the user sees.
                    if on_error == 'raise':
                        raise
                    break
                finally:
                    if cap.enabled:
                        assert cap.text is not None
                    # Ensure that we logged the output even in failure cases
                    self.logged_evals[partx] = got_eval
                    self.logged_stdout[partx] = cap.text

        if self.exc_info is None:
            self.failed_part = None

        if len(self._skipped_parts) == len(self._parts):
            # we skipped everything
            if self.mode == 'pytest':
                import pytest
                pytest.skip()

        summary = self._post_run(verbose)

        # Clear the global namespace so doctests don't leak memory
        self.global_namespace.clear()

        return summary

    @property
    def cmdline(self):
        """
        A cli-instruction that can be used to execute *this* doctest.

        Returns:
            str:
        """
        if self.mode == 'pytest':
            return 'pytest ' + self.node
        elif self.mode == 'native':
            ALLOW_MODNAME_CMDLINE = False
            if ALLOW_MODNAME_CMDLINE:
                # not 100% reliable if any dynamic code has executed before
                # or we are doing self-testing
                in_path = static.is_modname_importable(self.modname)
                if in_path:
                    # should be able to find the module by name
                    return 'python -m xdoctest ' + self.modname + ' ' + self.unique_callname
                else:
                    # needs the full path to be able to run the module
                    return 'python -m xdoctest ' + self.modpath + ' ' + self.unique_callname
            else:
                # Probably safer to always use the path
                return 'python -m xdoctest ' + self.modpath + ' ' + self.unique_callname
        else:
            raise KeyError(self.mode)

    @property
    def _block_prefix(self):
        return 'ZERO-ARG' if self.block_type == 'zero-arg' else 'DOCTEST'

    def _pre_run(self, verbose):
        if verbose >= 1:
            if verbose >= 2:
                barrier = self._color('====== <exec> ======', 'white')
                print(barrier)
            if self.block_type == 'zero-arg':
                # zero-arg funcs arent doctests, but we can still run them
                print('* ZERO-ARG FUNC : {}'.format(self.node))
            else:
                print('* DOCTEST : {}, line {}'.format(self.node, self.lineno) + self._color(' <- wrt source file', 'white'))
            if verbose >= 3:
                print(self._color(self._block_prefix + ' SOURCE', 'white'))
                print(self.format_src())
                print(self._color(self._block_prefix + ' STDOUT/STDERR', 'white'))

    def failed_line_offset(self):
        """
        Determine which line in the doctest failed.
        """
        if self.exc_info is None:
            return None
        else:
            ex_type, ex_value, tb = self.exc_info
            offset = self.failed_part.line_offset
            if isinstance(ex_value, checker.ExtractGotReprException):
                # Return the line of the "got" expression
                offset += self.failed_part.n_exec_lines
            elif isinstance(ex_value, checker.GotWantException):
                # Return the line of the want line
                offset += self.failed_part.n_exec_lines + 1
            else:
                offset += self.failed_tb_lineno
            offset -= 1
            return offset

    def failed_lineno(self):
        offset = self.failed_line_offset()
        if offset is None:
            return None
        else:
            # Find the first line of the part
            lineno = self.lineno + offset
            return lineno

    def repr_failure(self, with_tb=True):
        r"""
        Constructs lines detailing information about a failed doctest

        CommandLine:
            python -m xdoctest.core DocTest.repr_failure:0
            python -m xdoctest.core DocTest.repr_failure:1
            python -m xdoctest.core DocTest.repr_failure:2

        Example:
            >>> from xdoctest.core import *
            >>> docstr = utils.codeblock(
                '''
                >>> x = 1
                >>> print(x + 1)
                2
                >>> print(x + 3)
                3
                >>> print(x + 100)
                101
                ''')
            >>> parsekw = dict(fpath='foo.txt', callname='bar', lineno=42)
            >>> self = list(parse_docstr_examples(docstr, **parsekw))[0]
            >>> summary = self.run(on_error='return', verbose=0)
            >>> print('[res]' + '\n[res]'.join(self.repr_failure()))

        Example:
            >>> from xdoctest.core import *
            >>> docstr = utils.codeblock(
                r'''
                >>> 1
                1
                >>> print('.▴  .\n.▴ ▴.') # xdoc: -NORMALIZE_WHITESPACE
                . ▴ .
                .▴ ▴.
                ''')
            >>> parsekw = dict(fpath='foo.txt', callname='bar', lineno=42)
            >>> self = list(parse_docstr_examples(docstr, **parsekw))[0]
            >>> summary = self.run(on_error='return', verbose=1)
            >>> print('[res]' + '\n[res]'.join(self.repr_failure()))


        Example:
            >>> from xdoctest.core import *
            >>> docstr = utils.codeblock(
                '''
                >>> assert True
                >>> assert False
                >>> x = 100
                ''')
            >>> self = list(parse_docstr_examples(docstr))[0]
            >>> summary = self.run(on_error='return', verbose=0)
            >>> print('[res]' + '\n[res]'.join(self.repr_failure()))
        """
        #     '=== LINES ===',
        # ]

        # if '--xdoc-debug' in sys.argv:
        #     lines += ['DEBUG PARTS: ']
        #     for partx, part in enumerate(self._parts):
        #         lines += [str(partx) + ': ' + str(part)]
        #         lines += ['  directives: {!r}'.format(part.directives)]
        #         lines += ['  want: {!r}'.format(str(part.want)[0:25])]
        #         val = self.logged_evals.get(partx, None)
        #         lines += ['  eval: ' + repr(val)]
        #         val = self.logged_stdout.get(partx, None)
        #         lines += ['  stdout: ' + repr(val)]
        #     partx = self._parts.index(self.failed_part)
        #     lines += [
        #         'failed partx = {}'.format(partx)
        #     ]
        #     failed_part = self.failed_part
        #     lines += ['----']
        #     lines += ['Failed part line offset:']
        #     lines += ['{}'.format(failed_part.line_offset)]
        #     lines += ['Failed directives:']
        #     lines += ['{}'.format(list(failed_part.directives))]

        #     lines += ['Failed part source:']
        #     lines += failed_part.source.splitlines()
        #     lines += ['Failed part want:']
        #     if failed_part.want_lines:
        #         lines += failed_part.want_lines
        #     lines += ['Failed part stdout:']
        #     lines += self.logged_stdout[partx].splitlines()
        #     lines += ['Failed part eval:']
        #     lines += [repr(self.logged_evals[partx])]
        #     lines += ['----']

        #     lines += [
        #         # 'self.module = {}'.format(self.module),
        #         # 'self.modpath = {}'.format(self.modpath),
        #         # 'self.modpath = {}'.format(self.modname),
        #         # 'self.global_namespace = {}'.format(self.global_namespace.keys()),
        #     ]
        # lines += ['Failed doctest in ' + self.callname]

        if self.exc_info is None:
            return []
        ex_type, ex_value, tb = self.exc_info
        # Failure line offset wrt the doctest (starts from 0)
        fail_offset = self.failed_line_offset()
        # Failure line number wrt the entire file (starts from 1)
        fail_lineno = self.failed_lineno()

        lines = [
            '* REASON: {}'.format(ex_type.__name__),
            self._color(self._block_prefix + ' DEBUG INFO', 'white'),
            '  XDoc "{}", line {}'.format(self.node, fail_offset + 1) +
            self._color(' <- wrt doctest', 'red'),
        ]

        colored = self.config['colored']
        if fail_lineno is not None:
            fpath = self.UNKNOWN_FPATH if self.fpath is None else self.fpath
            lines += ['  File "{}", line {},'.format(fpath, fail_lineno) +
                      self._color(' <- wrt source file', 'red')]

        # lines += ['  in doctest "{}", line {}'.format(self.unique_callname,
        #                                               fail_offset + 1) +
        #           self._color(' <- relative line number in the docstest', 'red')]

        # source_text = self.format_src(colored=colored, linenos=True,
        #                               want=False)
        # source_text = utils.indent(source_text)
        # lines += source_text.splitlines()

        def r1_strip_nl(text):
            if text is None:
                return None
            return text[:-1] if text.endswith('\n') else text

        # if self.logged_stdout:
        #     lines += ['stdout results:']
        #     lines += [r1_strip_nl(t) for t in self.logged_stdout.values() if t]

        textgen = self.format_parts(colored=colored, linenos=True,
                                    want=False)

        n_digits = 1

        # Logic to break output between pass, failed, and unexecuted parts
        before_part_lines = []
        fail_part_lines = []
        after_parts_lines = []
        temp = [before_part_lines, fail_part_lines, after_parts_lines]
        tindex = 0
        indent_text = ' ' * (5 + n_digits)

        for partx, (part, part_text) in enumerate(zip(self._parts, textgen)):
            if part in self._skipped_parts:
                # temp[tindex] += [utils.indent(part_text, ' ' * 4)]
                # temp[tindex] += [utils.indent(' >>> # skipped', indent_text)]
                continue
            part_out = r1_strip_nl(self.logged_stdout.get(partx, ''))
            if part is self.failed_part:
                tindex += 1
            # Append the part source code
            temp[tindex] += [utils.indent(part_text, ' ' * 4)]
            # Append the part stdout (if it exists)
            if part_out:
                temp[tindex] += [utils.indent(part_out, indent_text)]
            if part is self.failed_part:
                tindex += 1
            # part_eval = self.logged_evals[partx]
            # if part_eval is not NOT_EVALED:
            #     temp[tindex] += [repr(part_eval)]

        lines += [self._color(self._block_prefix + ' PART BREAKDOWN', 'white')]
        if before_part_lines:
            lines += ['Passed Parts:']
            lines += before_part_lines

        if fail_part_lines:
            lines += ['Failed Part:']
            lines += fail_part_lines

        if after_parts_lines:
            lines += ['Remaining Parts:']
            lines += after_parts_lines

        lines += [self._color(self._block_prefix + ' TRACEBACK', 'white')]
        if hasattr(ex_value, 'output_difference'):
            lines += [
                ex_value.output_difference(self._runstate, colored=colored),
                ex_value.output_repr_difference(self._runstate)
            ]
        else:
            if with_tb:
                # TODO: enhance formatting to show an IPython-like output of
                # where the error occurred in the doctest
                tblines = traceback.format_exception(*self.exc_info)

                def _alter_traceback_linenos(self, tblines):

                    def overwrite_lineno(linepart):
                        # Replace the trailing part which is the lineno
                        old_linestr = linepart[-1]  # noqa

                        # This is the lineno we will insert
                        rel_lineno = self.failed_part.line_offset + tb_lineno
                        abs_lineno = self.lineno + rel_lineno - 1

                        new_linestr = 'rel: {rel}, abs: {abs}'.format(
                            rel=rel_lineno,
                            abs=abs_lineno,
                        )

                        linepart = linepart[:-1] + [new_linestr]
                        return linepart

                    new_tblines = []
                    for i, line in enumerate(tblines):

                        if 'xdoctest/xdoctest/doctest_example' in line:
                            # hack, remove ourselves from the tracback
                            continue
                            # new_tblines.append('!!!!!')
                            # raise Exception('foo')
                            # continue

                        if self._partfilename in line:
                            # Intercept the line corresponding to the doctest
                            tbparts = line.split(',')
                            tb_lineno = int(tbparts[-2].strip().split()[1])
                            # modify the line number to match the doctest
                            linepart = tbparts[-2].split(' ')

                            linepart = overwrite_lineno(linepart)

                            tbparts[-2] = ' '.join(linepart)
                            new_line = ','.join(tbparts)

                            # failed_ctx = '>>> ' + self.failed_part.exec_lines[tb_lineno - 1]
                            failed_ctx = self.failed_part.orig_lines[tb_lineno - 1]
                            extra = '    ' + failed_ctx
                            line = (new_line + extra + '\n')

                        # m = '(t{})'.format(i)
                        # line = m + line.replace('\n', '\n' + m)
                        new_tblines.append(line)

                    return new_tblines

                new_tblines = _alter_traceback_linenos(self, tblines)

                if colored:
                    tbtext = '\n'.join(new_tblines)
                    tbtext = utils.highlight_code(tbtext, lexer_name='pytb',
                                                  stripall=True)
                    new_tblines = tbtext.splitlines()
                lines += new_tblines

        lines += [self._color(self._block_prefix + ' REPRODUCTION', 'white')]
        lines += ['CommandLine:']
        lines += ['    ' + self.cmdline]
        return lines

    def _print_captured(self):
        out_text = ''.join([v for v in self.logged_stdout.values() if v])
        if out_text is not None:
            assert isinstance(out_text, six.text_type), 'do not use ascii'
        try:
            print(out_text)
        except UnicodeEncodeError:
            print('Weird travis bug')
            print('type(out_text) = %r' % (type(out_text),))
            print('out_text = %r' % (out_text,))

    def _color(self, text, color, enabled=None):
        """ conditionally color text based on config and flags """
        colored = self.config.getvalue('colored', enabled)
        if colored:
            text = utils.color_text(text, color)
        return text

    def _post_run(self, verbose):
        """
        Returns:
            Dict : summary
        """
        # print('POST RUN verbose = {!r}'.format(verbose))

        skipped = len(self._skipped_parts) == len(self._parts)
        failed = self.exc_info is not None
        passed = not failed and not skipped

        summary = {
            'exc_info': self.exc_info,
            'passed': passed,
            'skipped': skipped,
            'failed': failed,
        }

        if verbose >= 2:
            print(self._color(self._block_prefix + ' RESULT', 'white'))
        if self.exc_info is None:
            if verbose >= 1:
                if verbose >= 2:
                    if self._suppressed_stdout:
                        self._print_captured()
                if skipped:
                    success = self._color('SKIPPED', 'yellow')
                else:
                    success = self._color('SUCCESS', 'green')
                print('* {}: {}'.format(success, self.node))
        else:
            if verbose >= 1:
                failure = self._color('FAILURE', 'red')
                print('* {}: {}'.format(failure, self.node))

                if verbose >= 2:
                    lines = self.repr_failure()
                    text = '\n'.join(lines)
                    print(text)
        if verbose >= 2:
            barrier = self._color('====== </exec> ======', 'white')
            print(barrier)
        return summary


def _traverse_traceback(tb):
    # Lives down here to avoid issue calling exec in a function that contains a
    # nested function with free variable.  Not sure how necesary this is
    # because this doesn't have free variables.
    sub_tb = tb
    yield sub_tb
    while sub_tb.tb_next is not None:
        sub_tb = sub_tb.tb_next
        yield sub_tb


if __name__ == '__main__':
    r"""
    CommandLine:
        python -m xdoctest.doctest_example
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

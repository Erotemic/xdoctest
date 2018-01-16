# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import __future__
from collections import OrderedDict
import traceback
import textwrap
import warnings
import math
import sys
import re
import six
import itertools as it
from os.path import exists
from fnmatch import fnmatch
from xdoctest import static_analysis as static
from xdoctest import docscrape_google
from xdoctest import utils
from xdoctest import parser
from xdoctest import exceptions


NOT_EVALED = object()  # sentinal value


DOCTEST_STYLES = [
    'freeform',
    'google',
    # 'numpy',  # TODO
]


class ExitTestException(Exception):
    pass


class Config(dict):
    """
    Configuration for collection, execution, and reporting doctests
    """
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        self.update({
            'colored': True,
            # 'colored': False,
            'on_error': 'raise',
            'verbose': 1,
        })

    def getvalue(self, key, given=None):
        if given is None:
            return self[key]
        else:
            return given


class DocTest(object):
    """
    Holds information necessary to execute and verify a doctest

    Example:
        >>> from xdoctest import core
        >>> testables = core.parse_doctestables(core.__file__)
        >>> for test in testables:
        >>>     if test.callname == 'DocTest':
        >>>         self = test
        >>>         break
        >>> assert self.num == 0
        >>> assert self.modpath == core.__file__
        >>> print(self)
        <DocTest(xdoctest.core DocTest:0 ln ...)>
    """

    def __init__(self, docsrc, modpath=None, callname=None, num=0,
                 lineno=1, fpath=None, block_type=None, mode='pytest'):

        # if we know the google block type it is recorded
        self.block_type = block_type

        self.config = Config()

        self.modpath = modpath
        self.fpath = fpath
        if modpath is None:
            self.modname = '<modname?>'
            self.modpath = '<modpath?>'
        else:
            if fpath is not None:
                assert fpath == modpath, (
                    'only specify fpath for non-python files')
            self.fpath = modpath
            self.modname = static.modpath_to_modname(modpath)
        if callname is None:
            self.callname = '<callname?>'
        else:
            self.callname = callname
        self.docsrc = docsrc
        self.lineno = lineno
        self.num = num
        self._parts = None
        self.tb_lineno = None
        self.exc_info = None
        self.failed_part = None
        self.warn_list = None

        self.logged_evals = OrderedDict()
        self.logged_stdout = OrderedDict()

        self.module = None
        self.globs = {}
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
            # doctest: +SKIP
            # xdoctest: +SKIP

        And if running in pytest, you can also use
            # pytest.skip
        """
        disable_patterns = [
            r'>>>\s*#\s*DISABLE',
            r'>>>\s*#\s*UNSTABLE',
            r'>>>\s*#\s*FAILING',
            r'>>>\s*#\s*SCRIPT',
            r'>>>\s*#\s*x?doctest:\s\+SKIP',
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
                     offset_linenos=False):
        self._parse()
        colored = self.config.getvalue('colored', colored)

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
            part_text = part.format_src(linenos=linenos, want=want,
                                        startline=startline, n_digits=n_digits,
                                        colored=colored)
            yield part_text

    def format_src(self, linenos=True, colored=None, want=True,
                   offset_linenos=False):
        """
        Adds prefix and line numbers to a doctest

        Args:
            offset_linenos (bool): if True offset line numbers to agree with
                their position in the source text file (default False).

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
                                                offset_linenos=offset_linenos))
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
            >>> from xdoctest import docscrape_google
            >>> from xdoctest import core
            >>> docstr = core.DocTest._parse.__doc__
            >>> blocks = docscrape_google.split_google_docblocks(docstr)
            >>> doclineno = core.DocTest._parse.__code__.co_firstlineno
            >>> key, (docsrc, offset) = blocks[-2]
            >>> lineno = doclineno + offset
            >>> self = core.DocTest(docsrc, core.__file__, '_parse', 0, lineno)
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

    def _import_module(self):
        if self.module is None:
            if not self.modname.startswith('<'):
                self.module = utils.import_module_from_path(self.modpath)

    def _extract_future_flags(self, globs):
        """
        Return the compiler-flags associated with the future features that
        have been imported into the given namespace (globs).
        """
        compileflags = 0
        for key in __future__.all_feature_names:
            feature = globs.get(key, None)
            if feature is getattr(__future__, key):
                compileflags |= feature.compiler_flag
        return compileflags

    def _test_globals(self):
        test_globals = self.globs
        if self.module is None:
            compileflags = 0
        else:
            test_globals.update(self.module.__dict__)
            compileflags = self._extract_future_flags(test_globals)
        # force print function and division futures
        compileflags |= __future__.print_function.compiler_flag
        compileflags |= __future__.division.compiler_flag
        return test_globals, compileflags

    def run(self, verbose=None, on_error=None):
        """
        Executes the doctest
        """
        on_error = self.config.getvalue('on_error', on_error)
        verbose = self.config.getvalue('verbose', verbose)
        if on_error not in {'raise', 'return'}:
            raise KeyError(on_error)

        self._parse()  # parse out parts if we have not already done so
        self.pre_run(verbose)
        self._import_module()

        # Prepare for actual test run
        test_globals, compileflags = self._test_globals()

        self.logged_evals.clear()
        self.logged_stdout.clear()
        self.exc_info = None
        self._suppressed_stdout = verbose <= 1

        # Use the same capture object for all parts in the test
        cap = utils.CaptureStdout(supress=self._suppressed_stdout)
        with warnings.catch_warnings(record=True) as self.warn_list:
            for partx, part in enumerate(self._parts):

                # TODO: more sophisticated directive handling
                action = None
                for directive in part.directives:
                    if directive.name == 'SKIP' and directive.positive:
                        # inline mode skips just this line
                        # block mode applies to the remainder of parts
                        if directive.inline:
                            action = 'continue'
                        else:
                            action = 'break'
                    elif directive.name == 'REQUIRES' and directive.positive:
                        # same as SKIP if the requirement is not satisfied
                        if directive.args[0] not in sys.argv:
                            if directive.inline:
                                action = 'continue'
                            else:
                                action = 'break'
                if action == 'continue':
                    continue
                if action == 'break':
                    break

                # Prepare to capture stdout and evaluated values
                self.failed_part = part
                got_eval = NOT_EVALED
                try:
                    # Compile code, handle syntax errors
                    mode = 'eval' if part.use_eval else 'exec'

                    code = compile(
                        part.source, mode=mode,
                        filename='<doctest:' + self.node + '>',
                        flags=compileflags, dont_inherit=True
                    )
                except KeyboardInterrupt:  # nocover
                    raise
                except:
                    self.exc_info = sys.exc_info()
                    ex_type, ex_value, tb = self.exc_info
                    self.tb_lineno = tb.tb_lineno
                    if on_error == 'raise':
                        raise
                try:
                    # Execute the doctest code
                    with cap:
                        # NOTE: There is no difference between locals/globals in
                        # eval/exec context. Only pass in one dict, otherwise there
                        # is weird behavior
                        if part.use_eval:
                            # Only capture the repr to allow for gc tests
                            got_eval = eval(code, test_globals)
                        else:
                            exec(code, test_globals)

                    if part.want:
                        got_stdout = cap.text
                        part.check_got_vs_want(got_stdout, got_eval, NOT_EVALED)
                # Handle anything that could go wrong
                except KeyboardInterrupt:  # nocover
                    raise
                except ExitTestException:
                    if verbose > 0:
                        print('Test gracefully exists')
                    break
                except parser.GotWantException:
                    self.exc_info = sys.exc_info()
                    if on_error == 'raise':
                        raise
                    break
                except:
                    ex_type, ex_value, tb = sys.exc_info()
                    # CLEAN_TRACEBACK = True
                    CLEAN_TRACEBACK = 0
                    if CLEAN_TRACEBACK:
                        # Pop the eval off the stack
                        if tb.tb_next is not None:
                            tb = tb.tb_next
                        self.tb_lineno = tb.tb_lineno
                        # tb.tb_lineno = (tb_lineno +
                        #                 self.failed_part.line_offset + self.lineno)
                    else:
                        if tb.tb_next is None:
                            # TODO: test and understand this case
                            self.tb_lineno = tb.tb_lineno
                        else:
                            # Use the next to pop the eval of the stack
                            self.tb_lineno = tb.tb_next.tb_lineno

                    self.exc_info = (ex_type, ex_value, tb)
                    if on_error == 'raise':
                        raise
                    break
                finally:
                    assert cap.text is not None
                    self.logged_evals[partx] = got_eval
                    self.logged_stdout[partx] = cap.text

        if self.exc_info is None:
            self.failed_part = None
        return self.post_run(verbose)

    @property
    def cmdline(self):
        if self.mode == 'pytest':
            return 'pytest ' + self.node
        elif self.mode == 'native':
            return 'python -m ' + self.modname + ' ' + self.unique_callname
        else:
            raise KeyError(self.mode)

    def pre_run(self, verbose):
        if verbose >= 1:
            if verbose >= 2:
                if self.config['colored']:
                    print(utils.color_text('============', 'white'))
                else:
                    print('============')
            if self.block_type == 'zero-arg':
                # zero-arg funcs arent doctests, but we can still run them
                print('* ZERO-ARG FUNC : {}'.format(self.node))
            else:
                print('* BEGIN DOCTEST : {}'.format(self.node))
            if verbose >= 3:
                print(self.format_src())

    def failed_line_offset(self):
        """
        Determine which line in the doctest failed.
        """
        if self.exc_info is None:
            return None
        else:
            ex_type, ex_value, tb = self.exc_info
            offset = self.failed_part.line_offset
            if isinstance(ex_value, parser.GotWantException):
                # Return the line of the want line
                offset += self.failed_part.n_exec_lines + 1
            else:
                offset += self.tb_lineno
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

    def repr_failure(self):
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
            >>> print('\n'.join(self.repr_failure()))

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
            >>> print('\n'.join(self.repr_failure()))

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
            >>> print('\n'.join(self.repr_failure()))
        """
        #     '=== LINES ===',
        # ]

        # if '--xdoc-debug' in sys.argv:
        #     lines += ['DEBUG PARTS: ']
        #     for partx, part in enumerate(self._parts):
        #         lines += [str(partx) + ': ' + str(part)]
        #         lines += ['  use_eval: {!r}'.format(part.use_eval)]
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
        #         # 'self.globs = {}'.format(self.globs.keys()),
        #     ]
        # lines += ['Failed doctest in ' + self.callname]

        if self.exc_info is None:
            return []
        ex_type, ex_value, tb = self.exc_info
        fail_offset = self.failed_line_offset()
        fail_lineno = self.failed_lineno()

        lines = [
            'FAILED DOCTEST: {}'.format(ex_type.__name__),
            '  Node "{}"'.format(self.node),
        ]

        colored = self.config['colored']
        if fail_lineno is not None:
            fpath = '<file?>' if self.fpath is None else self.fpath
            lines += ['  File "{}", line {},'.format(fpath, fail_lineno)]

        lines += ['  in doctest "{}", line {}'.format(self.unique_callname,
                                                      fail_offset + 1)]

        # source_text = self.format_src(colored=colored, linenos=True,
        #                               want=False)
        # source_text = utils.indent(source_text)
        # lines += source_text.splitlines()

        def r1_strip_nl(text):
            return text[:-1] if text.endswith('\n') else text

        # if self.logged_stdout:
        #     lines += ['stdout results:']
        #     lines += [r1_strip_nl(t) for t in self.logged_stdout.values() if t]

        lines += ['Failed Part:']

        textgen = self.format_parts(colored=colored, linenos=True,
                                    want=False)

        n_digits = 1

        for partx, (part, part_text) in enumerate(zip(self._parts, textgen)):
            part_out = r1_strip_nl(self.logged_stdout[partx])
            lines += [utils.indent(part_text, ' ' * 4)]
            if part_out:
                lines += [utils.indent(part_out, ' ' * (5 + n_digits))]
            if part is self.failed_part:
                break
            # part_eval = self.logged_evals[partx]
            # if part_eval is not NOT_EVALED:
            #     lines += [repr(part_eval)]

        if hasattr(ex_value, 'output_difference'):
            # report_choice = _get_report_choice(
            #     self.config.getoption("doctestreport"))
            lines += [
                ex_value.output_difference(colored=colored),
                ('Repr:'),
                ('    ex_value.got  = {!r}'.format(ex_value.got)),
                ('    ex_value.want = {!r}'.format(ex_value.want)),
            ]
        else:
            tblines = traceback.format_exception(*self.exc_info)
            if colored:
                tbtext = '\n'.join(tblines)
                tbtext = utils.highlight_code(tbtext, lexer_name='pytb',
                                              stripall=True)
                tblines = tbtext.splitlines()
            lines += tblines

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

    def post_run(self, verbose):
        # print('POST RUN verbose = {!r}'.format(verbose))
        summary = {
            'passed': self.exc_info is None
        }
        colored = self.config['colored']
        if self.exc_info is None:
            if verbose >= 1:
                if self._suppressed_stdout:
                    self._print_captured()
                success = 'SUCCESS'
                if colored:
                    success = utils.color_text(success, 'green')
                print('* {}: {}'.format(success, self.node))
        else:
            if verbose >= 1:
                failure = 'FAILURE'
                if colored:
                    failure = utils.color_text(failure, 'red')
                print('* {}: {}'.format(failure, self.node))

                if verbose >= 2:
                    lines = self.repr_failure()
                    text = '\n'.join(lines)
                    print(text)
            summary['exc_info'] = self.exc_info
        return summary


def parse_freeform_docstr_examples(docstr, callname=None, modpath=None,
                                   lineno=1, fpath=None):
    """
    Finds free-form doctests in a docstring. This is similar to the original
    doctests because these tests do not requires a google/numpy style header.

    Some care is taken to avoid enabling tests that look like disabled google
    doctests / scripts.

    Raises:
        exceptions.DoctestParseError: if an error occurs in parsing

    Example:
        >>> from xdoctest import core
        >>> from xdoctest import utils
        >>> docstr = utils.codeblock(
            '''
            freeform
            >>> doctest
            >>> hasmultilines
            whoppie
            >>> 'butthis is the same doctest'

            >>> secondone

            Script:
                >>> 'special case, dont parse me'

            DisableDoctest:
                >>> 'special case, dont parse me'
                want

            AnythingElse:
                >>> 'general case, parse me'
                want
            ''')
        >>> examples = list(parse_freeform_docstr_examples(docstr))
        >>> assert len(examples) == 3

    """
    def doctest_from_parts(parts, num, curr_offset):
        nested = [
            p.orig_lines
            if p.want is None else
            p.orig_lines + p.want.splitlines()
            for p in parts
        ]
        docsrc = '\n'.join(list(it.chain.from_iterable(nested)))
        docsrc = textwrap.dedent(docsrc)
        example = DocTest(docsrc, modpath=modpath, callname=callname, num=num,
                          lineno=lineno + curr_offset, fpath=fpath)
        # rebase the offsets relative to the test lineno (ie start at 0)
        unoffset = parts[0].line_offset
        for p in parts:
            p.line_offset -= unoffset
        # We've already parsed the parts, so we dont need to do it again
        example._parts = parts
        return example

    respect_google_headers = True
    if respect_google_headers:
        # These are google doctest patterns that disable a test from being run
        # try to respect these even in freeform mode.
        special_skip_patterns = [
            'DisableDoctest:',
            'DisableExample:',
            'SkipDoctest:',
            'Ignore:',
            'Script:',
            'Sympy:',
        ]
    else:
        special_skip_patterns = []
    special_skip_patterns_ = tuple([
        p.lower() for p in special_skip_patterns
    ])

    def _start_ignoring(prev):
        return (special_skip_patterns_ and
                isinstance(prev, six.string_types) and
                prev.strip().lower().endswith(special_skip_patterns_))

    # parse into doctest and plaintext parts
    info = dict(callname=callname, modpath=modpath, lineno=lineno, fpath=fpath)
    all_parts = list(parser.DoctestParser().parse(docstr, info))

    curr_parts = []
    curr_offset = 0
    num = 0
    prev_part = None
    ignoring = False
    for part in all_parts:
        if isinstance(part, six.string_types):
            # Part is a plaintext
            if curr_parts:
                # Group the current parts into a single DocTest
                example = doctest_from_parts(curr_parts, num, curr_offset)
                yield example
                # Initialize empty parts for a new DocTest
                curr_offset += sum(p.n_lines for p in curr_parts)
                num += 1
                curr_parts = []
            curr_offset += part.count('\n') + 1
            # stop ignoring
            ignoring = False
        else:
            # If the previous part was text-based, and matches a special skip
            # ignore pattern then ignore all tests until a new doctest block
            # begins. (different doctest blocks are separated by plaintext)
            if ignoring or _start_ignoring(prev_part):
                ignoring = True
                curr_offset += part.n_lines
            else:
                # Append part to the current parts
                curr_parts.append(part)
        prev_part = part
    if curr_parts:
        # Group remaining parts into the final doctest
        example = doctest_from_parts(curr_parts, num, curr_offset)
        yield example


def parse_google_docstr_examples(docstr, callname=None, modpath=None, lineno=1,
                                 fpath=None, eager_parse=True):
    """
    Parses Google-style doctests from a docstr and generates example objects

    Raises:
        exceptions.MalformedDocstr: if an error occurs in finding google blocks
        exceptions.DoctestParseError: if an error occurs in parsing
    """
    blocks = docscrape_google.split_google_docblocks(docstr)
    example_blocks = []
    for type, block in blocks:
        if type.startswith('Example'):
            example_blocks.append((type, block))
        if type.startswith('Doctest'):
            example_blocks.append((type, block))
    for num, (type, (docsrc, offset)) in enumerate(example_blocks):
        # Add one because offset applies to the google-type label
        lineno_ = lineno + offset + 1
        example = DocTest(docsrc, modpath, callname, num, lineno=lineno_,
                          fpath=fpath, block_type=type)
        if eager_parse:
            # parse on the fly to be consistent with freeform?
            example._parse()
        yield example


def parse_docstr_examples(docstr, callname=None, modpath=None, lineno=1,
                          style='freeform', fpath=None):
    """
    Parses doctests from a docstr and generates example objects.
    The style influences which tests are found.
    """
    if style == 'freeform':
        parser = parse_freeform_docstr_examples
    elif style == 'google':
        parser = parse_google_docstr_examples
    # TODO:
    # elif style == 'numpy':
    #     parser = parse_numpy_docstr_examples
    else:
        raise KeyError('Unknown style={}. Valid styles are {}'.format(
            style, DOCTEST_STYLES))

    try:
        for example in parser(docstr, callname=callname, modpath=modpath,
                              fpath=fpath, lineno=lineno):
            yield example
    except Exception as ex:
        msg = ('Cannot scrape callname={} in modpath={} line={}.\n'
               'Caused by: {}\n')
        msg = msg.format(callname, modpath, lineno, repr(ex))
        if isinstance(ex, (exceptions.MalformedDocstr,
                           exceptions.DoctestParseError)):

            if isinstance(ex, exceptions.DoctestParseError):
                msg += '{}\n'.format(ex.string)
                msg += 'Original Error: {}\n'.format(repr(ex.orig_ex))

            warnings.warn(msg)  # doctest code contained errors
        else:
            raise Exception(msg)


def _rectify_to_modpath(modpath_or_name):
    """ if modpath_or_name is a name, statically converts it to a path """
    if exists(modpath_or_name):
        modpath = modpath_or_name
    else:
        modname = modpath_or_name
        modpath = static.modname_to_modpath(modname)
        assert modpath is not None, 'cannot find module={}'.format(modname)
    return modpath


def package_calldefs(modpath_or_name, exclude=[], ignore_syntax_errors=True):
    """
    Statically generates all callable definitions in a module or package

    Args:
        modpath_or_name (str): path to or name of the module to be tested

    Example:
        >>> modpath_or_name = 'xdoctest.core'
        >>> testables = list(package_calldefs(modpath_or_name))
        >>> assert len(testables) == 1
        >>> calldefs, modpath = testables[0]
        >>> assert static.modpath_to_modname(modpath) == modpath_or_name
        >>> assert 'package_calldefs' in calldefs
    """
    pkgpath = _rectify_to_modpath(modpath_or_name)

    modpaths = static.package_modpaths(pkgpath)
    for modpath in modpaths:
        modname = static.modpath_to_modname(modpath)
        if any(fnmatch(modname, pat) for pat in exclude):
            continue
        if not exists(modpath):
            warnings.warn(
                'Module {} does not exist. '
                'Is it an old pyc file?'.format(modname))
            continue
        try:
            calldefs = static.parse_calldefs(fpath=modpath)
        except SyntaxError as ex:
            # Handle error due to the actual code containing errors
            msg = 'Cannot parse module={} at path={}.\nCaused by: {}'
            msg = msg.format(modname, modpath, ex)
            if ignore_syntax_errors:
                warnings.warn(msg)  # real code contained errors
                continue
            else:
                raise SyntaxError(msg)
        else:
            yield calldefs, modpath


def parse_doctestables(modpath_or_name, exclude=[], style='google',
                       ignore_syntax_errors=True):
    """
    Parses all doctests within top-level callables of a module and generates
    example objects.  The style influences which tests are found.

    CommandLine:
        python -m xdoctest.core parse_doctestables

    Example:
        >>> modpath_or_name = 'xdoctest.core'
        >>> testables = list(parse_doctestables(modpath_or_name))
        >>> this_example = None
        >>> for example in testables:
        >>>     print(example)
        >>>     if example.callname == 'parse_doctestables':
        >>>         this_example = example
        >>> assert this_example is not None
        >>> assert this_example.callname == 'parse_doctestables'
    """

    if style not in DOCTEST_STYLES:
        raise KeyError('Unknown style={}. Valid styles are {}'.format(
            style, DOCTEST_STYLES))

    for calldefs, modpath in package_calldefs(modpath_or_name, exclude,
                                              ignore_syntax_errors):
        for callname, calldef in calldefs.items():
            docstr = calldef.docstr
            if calldef.docstr is not None:
                lineno = calldef.doclineno
                for example in parse_docstr_examples(docstr, callname=callname,
                                                     modpath=modpath,
                                                     lineno=lineno,
                                                     style=style):
                    yield example


if __name__ == '__main__':
    """
    CommandLine:
        python -m xdoctest.core
    """
    import xdoctest as xdoc
    xdoc.doctest_module()

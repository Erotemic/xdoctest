# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import __future__
import textwrap
import warnings
import sys
import re
import six
import itertools as it
from os.path import exists
from xdoctest import static_analysis as static
from xdoctest import docscrape_google
from xdoctest import utils
from xdoctest import parser


class ExitTestException(Exception):
    pass


class DocTest(object):
    """
    Holds information necessary to execute and verify a doctest

    Example:
        >>> from xdoctest import core
        >>> testables = core.module_doctestables(core.__file__)
        >>> for test in testables:
        >>>     if test.callname == 'DocTest':
        >>>         self = test
        >>>         break
        >>> assert self.num == 0
        >>> assert self.modpath == core.__file__
        >>> print(self.valid_testnames)
    """

    def __init__(self, docsrc, modpath=None, callname=None, num=0,
                 lineno=1, fpath=None):
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
        self.exc_info = None
        self.failed_part = None
        self.stdout_results = []
        self.evaled_results = []
        self.globs = {}

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

    def is_disabled(self):
        """
        Checks for comment directives on the first line of the doctest
        """
        m = re.match(r'>>>\s*#\s*DISABLE', self.docsrc, flags=re.IGNORECASE)
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

    def format_src(self, linenos=True, colored=False, want=True,
                   offset_linenums=False):
        """
        Adds prefix and line numbers to a doctest

        Example:
            >>> from xdoctest import core
            >>> testables = module_doctestables(core.__file__)
            >>> self = next(testables)
            >>> self._parse()
            >>> print(self.format_src())
            >>> print(self.format_src(linenos=False, colored=False))
            >>> assert not self.is_disabled()
        """
        import math
        # return '\n'.join([p.source for p in self._parts])
        formated_parts = []

        if linenos:
            if offset_linenums:
                startline = 1 if self.lineno is None else self.lineno
            else:
                startline = 1
            n_lines = sum(p.n_lines for p in self._parts)
            endline = startline + n_lines

            n_digits = math.log(max(1, endline), 10)
            n_digits = int(math.ceil(n_digits))

            src_fmt = '{{:{}d}} {{}}'.format(n_digits)
            want_fmt = '{} {{}}'.format(' ' * n_digits)

        for part in self._parts:
            doctest_src = part.source
            doctest_src = utils.indent(doctest_src, '>>> ')
            # doctest_src = '\n'.join(part.orig_lines)
            # doctest_src = '\n'.join(part.orig_lines)
            doctest_want = part.want if part.want else ''

            parser

            if linenos:
                new_lines = []
                count = startline + part.line_offset
                for count, line in enumerate(doctest_src.splitlines(), start=count):
                    new_lines.append(src_fmt.format(count, line))
                if doctest_want:
                    for count, line in enumerate(doctest_want.splitlines(), start=count):
                        if want:
                            new_lines.append(want_fmt.format(line))
                new = '\n'.join(new_lines)
            else:
                if doctest_want:
                    new = doctest_src
                    if want:
                        new = new + '\n' + doctest_want
                else:
                    new = doctest_src
            if colored:
                new = utils.highlight_code(new, 'python')
            formated_parts.append(new)
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
            self._parts = parser.DoctestParser().parse(self.docsrc)
            self._parts = [p for p in self._parts
                           if not isinstance(p, six.string_types)]

    def run(self, verbose=None, on_error=None):
        """
        Executes the doctest

        TODO:
            * break src and want into multiple parts

        Notes:
            * There is no difference between locals/globals in exec context
            Only pass in one dict, otherwise there is weird behavior
        """
        if on_error is None:
            on_error = 'raise'
        if on_error not in {'raise', 'return'}:
            raise KeyError(on_error)

        if verbose is None:
            verbose = 1
        self._parse()
        self.pre_run(verbose)
        # Prepare for actual test run
        test_globals = self.globs

        if not self.modname.startswith('<'):
            # TODO:
            # Put the module globals in the doctest global namespace
            # Import from the filepath?
            # module = utils.import_module_from_fpath(self.modpath)
            module = utils.import_module_from_name(self.modname)
            # module = __import__(self.modname, {}, {})
            self.module = module
            test_globals.update(module.__dict__)
            compileflags = 0
        else:
            self.module = None
            # else:
            #     if self.fname is not None:
            #         if '__file__' not in test_globals:
            #             test_globals['__file__'] = self.fpath

            def _extract_future_flags(globs):
                """
                Return the compiler-flags associated with the future features that
                have been imported into the given namespace (globs).
                """
                flags = 0
                for fname in __future__.all_feature_names:
                    feature = globs.get(fname, None)
                    if feature is getattr(__future__, fname):
                        flags |= feature.compiler_flag
                return flags

            compileflags = _extract_future_flags(test_globals)
        self.stdout_results = []
        self.evaled_results = []
        self.exc_info = None

        not_evaled = object()  # sentinal value

        for part in self._parts:
            # Prepare to capture stdout and evaluated values
            self.failed_part = part
            got_eval = not_evaled
            cap = utils.CaptureStdout(supress=verbose <= 1)
            try:
                # Compile code, handle syntax errors
                mode = 'eval' if part.use_eval else 'exec'

                code = compile(
                    part.source, mode=mode,
                    filename=self.node,
                    flags=compileflags, dont_inherit=True
                )
            except KeyboardInterrupt:  # nocover
                raise
            except:
                self.exc_info = sys.exc_info()
                if on_error == 'raise':
                    raise
            try:
                # Execute the doctest code
                with cap:
                    if part.use_eval:
                        # Only capture the repr to allow for gc tests
                        got_eval = eval(code, test_globals)
                        self.evaled_results.append(repr(got_eval))
                    else:
                        exec(code, test_globals)
                        self.evaled_results.append(None)
                if part.want:
                    got_stdout = cap.text
                    part.check_got_vs_want(got_stdout, got_eval, not_evaled)
            # Handle anything that could go wrong
            except KeyboardInterrupt:  # nocover
                raise
            except ExitTestException:  # nocover
                if verbose > 0:
                    print('Test gracefully exists')
            except parser.GotWantException:
                self.exc_info = sys.exc_info()
                if on_error == 'raise':
                    raise
                break
            except:
                # import traceback
                # print("Got exception:", traceback.format_exc())
                self.exc_info = sys.exc_info()
                if on_error == 'raise':
                    raise
                break
            finally:
                assert cap.text is not None
                self.stdout_results.append(cap.text)

        if self.exc_info is None:
            self.failed_part = None
        return self.post_run(verbose)

    @property
    def cmdline(self):
        # TODO: move to pytest
        return 'python -m ' + self.modname + ' ' + self.unique_callname

    def pre_run(self, verbose):
        if verbose >= 1:
            if verbose >= 2:
                print('============')
            print('* DOCTEST : {}'.format(self.callname))
            # print(self.cmdline)
            if verbose >= 2:
                print(self.format_src())
        else:  # nocover
            sys.stdout.write('.')
            sys.stdout.flush()

    def failed_line_offset(self):
        if self.exc_info is None:
            return None
        else:
            from xdoctest import parser
            type, value, tb = self.exc_info
            offset = self.failed_part.line_offset
            if isinstance(value, parser.GotWantException):
                # Return the line of the want line
                offset += self.failed_part.n_lines
            else:
                # Use the next because we need to pop the eval of the stack
                if tb.tb_next is None:
                    offset = tb.tb_lineno
                else:
                    offset += tb.tb_next.tb_lineno
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

    def repr_failure(self, verbose=1, colored=True):
        """
        Notes:
            utool's output format was

            (stdout was printed in real time)
            test-stdout,
            errmsg + traceback

            Then failed where:
                docest src


        """
        type, value, tb = self.exc_info
        fail_offset = self.failed_line_offset()
        fail_lineno = self.failed_lineno()

        lines = [
            'FAILED DOCTEST: {}'.format(type.__name__),
            'in node ' + self.node,
        ]
        #     '=== LINES ===',
        # ]

        lines += [
            # 'self.module = {}'.format(self.module),
            # 'self.modpath = {}'.format(self.modpath),
            # 'self.modpath = {}'.format(self.modname),
            # 'self.globs = {}'.format(self.globs.keys()),
        ]

        # lines += ['Failed doctest in ' + self.callname]

        source_text = self.format_src(colored=colored, linenos=True,
                                      want=False)
        if fail_lineno is not None:
            lines += ['in {} on line {}'.format(self.fpath, fail_lineno)]
        lines += ['in docsrc on line {}'.format(fail_offset + 1)]

        source_text = utils.indent(source_text)
        lines += source_text.splitlines()

        if self.stdout_results:
            lines += self.stdout_results

        #     # '=== LINES ===',
        #     'lineno = {!r}'.format(lineno),
        #     # 'example.lineno = {!r}'.format(self.lineno),
        #     # 'example.failed_part.line_offset = {!r}'.format(self._parts[0].line_offset),
        #     # 'self._parts = {!r}'.format(self._parts)
        #     # repr(excinfo),
        #     # str(value),
        #     # str(message),
        # ]

        if hasattr(value, 'output_difference'):
            # report_choice = _get_report_choice(self.config.getoption("doctestreport"))
            lines += [
                value.output_difference()
            ]
        else:
            import traceback
            tblines = traceback.format_exception(*self.exc_info)
            if colored:
                tbtext = '\n'.join(tblines)
                tbtext = utils.highlight_code(tbtext, lexer_name='pytb',
                                              stripall=True)
                tblines = tbtext.splitlines()
            lines += tblines
        return lines

    def _print_captured(self):
        out_text = ''.join(self.stdout_results)
        if out_text is not None:
            assert isinstance(out_text, six.text_type), 'do not use ascii'
        try:
            print(out_text)
        except UnicodeEncodeError:
            print('Weird travis bug')
            print('type(out_text) = %r' % (type(out_text),))
            print('out_text = %r' % (out_text,))

    def post_run(self, verbose):
        summary = {
            'passed': self.exc_info is None
        }
        if self.exc_info is None:
            if verbose >= 1:
                print('* SUCCESS: {}'.format(self.callname))
                self._print_captured()
        else:
            if verbose >= 1:
                text = '\n'.join(self.repr_failure(verbose=verbose))
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
    all_parts = parser.DoctestParser().parse(docstr)

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


def parse_google_docstr_examples(docstr, callname=None, modpath=None,
                                 lineno=None):
    """
    Parses Google-style doctests from a docstr and generates example objects

    TODO: generalize to not just google-style
    """
    try:
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
            example = DocTest(docsrc, modpath, callname, num, lineno=lineno_)
            yield example
    except Exception as ex:  # nocover
        msg = ('Cannot scrape callname={} in modpath={}.\n'
               'Caused by={}')
        msg = msg.format(callname, modpath, ex)
        raise Exception(msg)


def module_calldefs(modpath):
    return static.parse_calldefs(fpath=modpath)


def package_calldefs(package_name, exclude=[], strict=False):
    """
    Statically generates all callable definitions in a package
    """
    modnames = static.package_modnames(package_name, exclude=exclude)
    for modname in modnames:
        modpath = static.modname_to_modpath(modname, hide_init=False)
        if not exists(modpath):  # nocover
            warnings.warn(
                'Module {} does not exist. '
                'Is it an old pyc file?'.format(modname))
            continue
        try:
            calldefs = module_calldefs(modpath=modpath)
        except SyntaxError as ex:  # nocover
            msg = 'Cannot parse module={} at path={}.\nCaused by={}'
            msg = msg.format(modname, modpath, ex)
            if strict:
                raise Exception(msg)
            else:
                warnings.warn(msg)
                continue
        else:
            yield calldefs, modpath


def module_doctestables(modpath, mode='freeform'):
    if mode == 'freeform':
        parser = parse_freeform_docstr_examples
    elif mode == 'google':
        parser = parse_google_docstr_examples
    else:
        raise KeyError(mode)

    calldefs = module_calldefs(modpath)
    for callname, calldef in calldefs.items():
        docstr = calldef.docstr
        if calldef.docstr is not None:
            lineno = calldef.doclineno
            for example in parser(docstr, callname, modpath, lineno=lineno):
                yield example


def parse_doctestables(package_name, exclude=[], strict=False):
    r"""
    Finds all functions/callables with Google-style example blocks

    DisableExample:
        >>> package_name = 'xdoctest'
        >>> testables = list(parse_doctestables(package_name))
        >>> this_example = None
        >>> for example in testables:
        >>>     print(example)
        >>>     if example.callname == 'parse_doctestables':
        >>>         this_example = example
        >>> assert this_example is not None
        >>> assert this_example.callname == 'parse_doctestables'
    """
    for calldefs, modpath in package_calldefs(package_name, exclude, strict):
        for callname, calldef in calldefs.items():
            docstr = calldef.docstr
            if calldef.docstr is not None:
                lineno = calldef.doclineno
                for example in parse_google_docstr_examples(docstr, callname,
                                                            modpath,
                                                            lineno=lineno):
                    yield example

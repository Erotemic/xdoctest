# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import warnings
import sys
import six
from os.path import exists
from doctest2 import static_analysis as static
from doctest2 import docscrape_google
from doctest2 import utils
from doctest2 import doctest_parser


class ExitTestException(Exception):
    pass


class DocTest(object):
    """
    Holds information necessary to execute and verify a doctest

    Example:
        >>> package_name = 'doctest2'
        >>> testables = parse_doctestables(package_name)
        >>> self = next(testables)
        >>> print(self.want)
        >>> print(self.want)
        >>> print(self.valid_testnames)
    """

    def __nice__(self):
        return self.modname + ' ' + self.callname

    def __init__(self, modpath, callname, docsrc, num, lineno=0):
        self.modpath = modpath
        self.modname = static.modpath_to_modname(modpath)
        self.callname = callname
        self.docsrc = docsrc
        self.lineno = lineno
        self.num = num
        self._parts = None
        self.ex = None
        self.outputs = []
        self.globs = {}

    def is_disabled(self):
        return self.docsrc.startswith('>>> # DISABLE_DOCTEST')

    @property
    def unique_callname(self):
        return self.callname + ':' + str(self.num)

    @property
    def valid_testnames(self):
        return {
            self.callname,
            self.unique_callname,
        }

    def format_src(self, linenums=True, colored=True):
        """
        Adds prefix and line numbers to a doctest

        Example:
            >>> package_name = 'doctest2'
            >>> testables = parse_doctestables(package_name)
            >>> self = next(testables)
            >>> print(self.format_src())
            >>> print(self.format_src(linenums=False, colored=False))
            >>> assert not self.is_disabled()
        """
        # return '\n'.join([p.source for p in self._parts])
        part_source = []
        for part in self._parts:
            doctest_src = part.source
            doctest_src = utils.indent(doctest_src, '>>> ')
            if linenums:
                doctest_src = '\n'.join([
                    '%3d %s' % (count, line)
                    for count, line in enumerate(
                        doctest_src.splitlines(), start=1 + part.line_offset)])
            if colored:
                doctest_src = utils.highlight_code(doctest_src, 'python')
            part_source.append(doctest_src)
        full_source = '\n'.join(part_source)
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
            >>> from doctest2 import doctest_parser
            >>> from doctest2 import docscrape_google
            >>> from doctest2 import core
            >>> docstr = core.DocTest._parse.__doc__
            >>> blocks = docscrape_google.split_google_docblocks(docstr)
            >>> doclineno = core.DocTest._parse.__code__.co_firstlineno
            >>> key, (docsrc, offset) = blocks[-2]
            >>> lineno = doclineno + offset
            >>> self = core.DocTest(core.__file__, '_parse',  docsrc, 0, lineno)
            >>> self._parse()
            >>> assert len(self._parts) == 3
            >>> p1, p2, p3 = self._parts
            >>> self.run()
        """
        self._parts = doctest_parser.DoctestParser().parse(self.docsrc)
        self._parts = [p for p in self._parts
                       if not isinstance(p, six.string_types)]

    def run(self, verbose=None):
        """
        Executes the doctest

        TODO:
            * break src and want into multiple parts

        Notes:
            * There is no difference between locals/globals in exec context
            Only pass in one dict, otherwise there is weird behavior
            References: https://bugs.python.org/issue13557
        """
        if verbose is None:
            verbose = 2
        self._parse()
        self.pre_run(verbose)
        # Prepare for actual test run
        test_globals = self.globs
        self.outputs = []
        try:
            for part in self._parts:
                code = compile(part.source, '<string>', 'exec')
                cap = utils.CaptureStdout(supress=verbose <= 1)
                with cap:
                    exec(code, test_globals)
                assert cap.text is not None
                self.outputs.append(cap.text)
                part.check_got_vs_want(cap.text)
        # Handle anything that could go wrong
        except ExitTestException:  # nocover
            if verbose > 0:
                print('Test gracefully exists')
        except Exception as ex:  # nocover
            self.ex = ex
            self.report_failure(verbose)
            raise

        return self.post_run(verbose)

    @property
    def cmdline(self):
        # TODO: move to pytest
        return 'python -m ' + self.modname + ' ' + self.unique_callname

    def pre_run(self, verbose):
        if verbose >= 1:
            print('============')
            print('* BEGIN EXAMPLE : {}'.format(self.callname))
            print(self.cmdline)
            if verbose >= 2:
                print(self.format_src())
        else:  # nocover
            sys.stdout.write('.')
            sys.stdout.flush()

    def repr_failure(self, verbose=1):
        # TODO: print out nice line number
        lines = []
        if verbose > 0:
            lines += [
                '',
                'report failure',
                self.cmdline,
                self.format_src(),
            ]
        lines += [
            '* FAILURE: {}, {}'.format(self.callname, type(self.ex)),
            ''.join(self.outputs),
        ]
        # TODO: remove appropriate amount of traceback
        # exc_type, exc_value, exc_traceback = sys.exc_info()
        # exc_traceback = exc_traceback.tb_next
        # six.reraise(exc_type, exc_value, exc_traceback)
        return '\n'.join(lines)

    def report_failure(self, verbose):
        text = self.repr_failure(verbose=verbose)
        print(text)

    def post_run(self, verbose):
        if self.ex is None and verbose >= 1:
            # out_text = ''.join(self.outputs)
            # if out_text is not None:
            #     assert isinstance(out_text, six.text_type), 'do not use ascii'
            # try:
            #     print(out_text)
            # except UnicodeEncodeError:
            #     print('Weird travis bug')
            #     print('type(out_text) = %r' % (type(out_text),))
            #     print('out_text = %r' % (out_text,))
            print('* SUCCESS: {}'.format(self.callname))
        summary = {
            'passed': self.ex is None
        }
        return summary


def parse_google_docstr_examples(docstr, callname=None, modpath=None,
                                 lineno=None):
    """
    Parses Google-style doctests from a docstr and generates example objects
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
            example = DocTest(modpath, callname, docsrc, num, lineno=lineno_)
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
            calldefs = module_calldefs(fpath=modpath)
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


def parse_doctestables(package_name, exclude=[], strict=False):
    r"""
    Finds all functions/callables with Google-style example blocks

    Example:
        >>> package_name = 'doctest2'
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
                for example in parse_google_docstr_examples(docstr, callname, modpath, lineno=lineno):
                    yield example

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

    def __init__(self, modpath, callname, block, num, lineno=0):
        self.modpath = modpath
        self.modname = static.modpath_to_modname(modpath)
        self.callname = callname
        self.block = block
        self.lineno = lineno
        self.num = num
        self._src = None
        self._want = None
        self.ex = None
        self.cap = None
        self.globs = {}

    @property
    def src(self):
        if self._src is None:
            self._parse()
        return self._src

    @property
    def want(self):
        if self._want is None:
            self._parse()
        return self._want

    def _parse(self):
        self._parts = doctest_parser.DoctestParser().parse(self.block)

    def is_disabled(self):
        return self.block.startswith('>>> # DISABLE_DOCTEST')

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
        doctest_src = self.src
        doctest_src = utils.indent(doctest_src, '>>> ')
        if linenums:
            doctest_src = '\n'.join([
                '%3d %s' % (count, line)
                for count, line in enumerate(doctest_src.splitlines(), start=1)])
        if colored:
            from doctest2 import colors
            doctest_src = colors.highlight_code(doctest_src, 'python')
        return doctest_src

    def run_example(self, verbose=None):
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
        self.cap = utils.CaptureStdout(enabled=verbose <= 1)
        code = compile(self.src, '<string>', 'exec')
        try:
            with self.cap:
                exec(code, test_globals)
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
            self.cap.text,
        ]
        # TODO: remove appropriate amount of traceback
        # exc_type, exc_value, exc_traceback = sys.exc_info()
        # exc_traceback = exc_traceback.tb_next
        # six.reraise(exc_type, exc_value, exc_traceback)
        return '\n'.join(lines)

    def report_failure(self, verbose):  # nocover
        self.repr_failure(verbose=verbose)

    def post_run(self, verbose):  # nocover
        if self.ex is None and verbose >= 1:
            if self.cap.text is not None:  # nocover
                assert isinstance(self.cap.text, six.text_type), 'do not use ascii'
            try:
                print(self.cap.text)
            except UnicodeEncodeError:  # nocover
                print('Weird travis bug')
                print('type(cap.text) = %r' % (type(self.cap.text),))
                print('cap.text = %r' % (self.cap.text,))
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
        for type_, block in blocks:
            if type_.startswith('Example'):
                example_blocks.append((type_, block))
            if type_.startswith('Doctest'):
                example_blocks.append((type_, block))
        for num, (type_, block) in enumerate(example_blocks):
            example = DocTest(modpath, callname, block, num)
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

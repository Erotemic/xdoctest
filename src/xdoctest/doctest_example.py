"""
This module defines the main class that holds a DocTest example
"""

from __future__ import annotations
import __future__

import ast
from fnmatch import fnmatch
import math
import os
import re
import sys
import traceback
import types
import typing
import warnings
from collections import OrderedDict
from inspect import CO_COROUTINE
from typing import TYPE_CHECKING, Any, Union, cast

importlib_metadata_compat: types.ModuleType

try:
    from importlib import metadata as importlib_metadata
except ImportError:  # nocover
    import importlib_metadata as importlib_metadata_compat  # type: ignore[import-not-found]
else:
    importlib_metadata_compat = importlib_metadata

try:
    from packaging.requirements import Requirement
except ImportError:  # nocover
    Requirement = None  # type: ignore

from xdoctest import (  # NOQA
    checker,
    constants,
    directive,
    exceptions,
    global_state,
    parser,
    utils,
)

if TYPE_CHECKING:
    from xdoctest.doctest_part import DoctestPart

from xdoctest import static_analysis as static  # NOQA

__devnotes__ = """
TODO:
    - [ ] Rename DocTest to Doctest? - Probably not, its been years.
    - [ ] I dont like having "example" as a suffix to this modname, can we rename? - Probably not, its been years.
"""


class DoctestConfig(dict):
    """
    Doctest configuration

    Static configuration for collection, execution, and reporting doctests.
    Note dynamic directives are not managed by DoctestConfig, they use
    RuntimeState.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(DoctestConfig, self).__init__(*args, **kwargs)
        self.update(
            {
                # main options exposed by command line runner/plugin
                'colored': hasattr(sys.stdout, 'isatty')
                and sys.stdout.isatty(),
                'reportchoice': 'udiff',
                'default_runtime_state': {},
                'offset_linenos': False,
                'deferred_output_matching': True,
                'global_exec': None,
                'optional_want': True,
                'supress_import_errors': False,
                'on_error': 'raise',
                'partnos': False,
                'verbose': 1,
            }
        )

    def _populate_from_cli(self, ns):
        from xdoctest.directive import parse_directive_optstr

        directive_optstr = ns['options']
        default_runtime_state = {}
        if directive_optstr:
            for optpart in directive_optstr.split(','):
                directive = parse_directive_optstr(optpart)
                if directive is None:
                    raise Exception(
                        'Failed to parse directive given in the xdoctest "options"'
                        'directive_optstr={!r}'.format(directive_optstr)
                    )
                default_runtime_state[directive.name] = directive.positive
        _examp_conf = {
            'default_runtime_state': default_runtime_state,
            'deferred_output_matching': ns['deferred_output_matching'],
            'offset_linenos': ns['offset_linenos'],
            'colored': ns['colored'],
            'reportchoice': ns['reportchoice'],
            'global_exec': ns['global_exec'],
            'optional_want': ns['optional_want'],
            'supress_import_errors': ns['supress_import_errors'],
            'verbose': ns['verbose'],
        }
        return _examp_conf

    def _update_argparse_cli(
        self,
        add_argument: typing.Callable[..., typing.Any],
        prefix: str | list[str] | None = None,
        defaults: dict[str, typing.Any] = {},
    ) -> None:
        """
        Updates a pytest or argparse CLI

        Args:
            add_argument (callable): the parser.add_argument function
        """
        import argparse

        def str_lower(x: str) -> str:
            # python2 fix
            return str.lower(str(x))

        add_argument_kws: list[tuple[list[str], dict[str, Any]]] = [
            (
                ['--colored'],
                dict(
                    dest='colored',
                    default=self['colored'],
                    help=('Enable or disable ANSI coloration in stdout'),
                ),
            ),
            (
                ['--nocolor'],
                dict(
                    dest='colored',
                    action='store_false',
                    default=argparse.SUPPRESS,
                    help=('Disable ANSI coloration in stdout'),
                ),
            ),
            (
                ['--offset'],
                dict(
                    dest='offset_linenos',
                    action='store_true',
                    default=self['offset_linenos'],
                    help=(
                        'If True formatted source linenumbers will agree with '
                        'their location in the source file. Otherwise they '
                        'will be relative to the doctest itself.'
                    ),
                ),
            ),
            (
                ['--deferred-output-matching'],
                dict(
                    dest='deferred_output_matching',
                    action='store_true',
                    default=self['deferred_output_matching'],
                    help=(
                        'Allow stdout from no-want parts to be matched by a '
                        'later want-bearing part'
                    ),
                ),
            ),
            (
                ['--no-deferred-output-matching'],
                dict(
                    dest='deferred_output_matching',
                    action='store_false',
                    default=argparse.SUPPRESS,
                    help=('Disable deferred stdout matching between parts'),
                ),
            ),
            (
                ['--report'],
                dict(
                    dest='reportchoice',
                    type=str_lower,
                    choices=(
                        'none',
                        'cdiff',
                        'ndiff',
                        'udiff',
                        'only_first_failure',
                    ),
                    default=self['reportchoice'],
                    help=(
                        'Choose another output format for diffs on xdoctest failure'
                    ),
                ),
            ),
            # used to build default_runtime_state
            (
                ['--options'],
                dict(
                    type=str_lower,
                    default=None,
                    dest='options',
                    help='Default directive flags for doctests',
                ),
            ),
            (
                ['--global-exec'],
                dict(
                    type=str,
                    default=None,
                    dest='global_exec',
                    help='Custom Python code to execute before every test',
                ),
            ),
            (
                ['--optional-want'],
                dict(
                    dest='optional_want',
                    action='store_true',
                    default=self['optional_want'],
                    help='Allow parts to omit local want output',
                ),
            ),
            (
                ['--no-optional-want'],
                dict(
                    dest='optional_want',
                    action='store_false',
                    default=argparse.SUPPRESS,
                    help='Require each output-producing part to have a want',
                ),
            ),
            # FIXME: this has a spelling error
            (
                ['--supress-import-errors'],
                dict(
                    dest='supress_import_errors',
                    action='store_true',
                    default=self['supress_import_errors'],
                    help='Removes tracebacks from errors in implicit imports',
                ),
            ),
            (
                ['--verbose'],
                dict(
                    type=int,
                    default=defaults.get('verbose', 3),
                    dest='verbose',
                    help=(
                        'Verbosity level. '
                        '0 is silent, '
                        '1 prints out test names, '
                        '2 additionally prints test stdout, '
                        '3 additionally prints test source'
                    ),
                ),
            ),
            (
                ['--quiet'],
                dict(
                    action='store_true',
                    dest='verbose',
                    default=argparse.SUPPRESS,
                    help='sets verbosity to 1',
                ),
            ),
            (
                ['--silent'],
                dict(
                    action='store_false',
                    dest='verbose',
                    default=argparse.SUPPRESS,
                    help='sets verbosity to 0',
                ),
            ),
        ]

        if prefix is None:
            prefix = ['']
        # mypy: after this point prefix should be a list of strings
        assert isinstance(prefix, list)

        # TODO: make environment variables as args more general
        import os

        environ_aware = {
            'deferred-output-matching',
            'optional-want',
            'report',
            'options',
            'global-exec',
            'verbose',
        }
        for alias, kw in add_argument_kws:
            # Use environment variables for some defaults
            argname = alias[0].lstrip('-')
            if argname in environ_aware:
                env_argname = 'XDOCTEST_' + argname.replace('-', '_').upper()
                if 'default' in kw:
                    kw['default'] = os.environ.get(env_argname, kw['default'])

            alias = [
                a.replace('--', '--' + p + '-') if p else a
                for a in alias
                for p in prefix
            ]
            if prefix[0]:
                kw['dest'] = f'{prefix[0]}_{kw["dest"]}'
            add_argument(*alias, **kw)

    def getvalue(self, key: str, given: typing.Any = None) -> object:
        """
        Args:
            key (str): The configuration key
            given (Any): A user override

        Returns:
            Any: if given is None returns the configured value
        """
        if given is None:
            return self[key]
        else:
            return given


def _doctest_requirement_satisfied(requirement_text: str) -> bool:
    """
    Return True when a doctestplus-style requirement is satisfied.
    """
    if Requirement is None:
        raise ImportError(
            'packaging is required to evaluate __doctest_requires__'
        )

    try:
        requirement = Requirement(requirement_text)
    except Exception as ex:
        raise ValueError(
            'Invalid __doctest_requires__ requirement: {!r}'.format(
                requirement_text
            )
        ) from ex

    try:
        installed_version = importlib_metadata_compat.version(requirement.name)
    except Exception:
        installed_version = None

    if not requirement.specifier:
        if installed_version is not None:
            return True
        from importlib.util import find_spec

        return find_spec(requirement.name) is not None

    if installed_version is None:
        return False
    return requirement.specifier.contains(installed_version, prereleases=True)


class DocTest:
    """
    Holds information necessary to execute and verify a doctest

    Attributes:

        docsrc (str):
            doctest source code

        modpath (str | PathLike | None):
            module the source was read from

        callname (str):
            name of the function/method/class/module being tested

        num (int):
            the index of the doctest in the docstring. (i.e. this object
            refers to the num-th doctest within a docstring)

        lineno (int):
            The line (starting from 1) in the file that the doctest begins on.
            (i.e. if you were to go to this line in the file, the first line of
            the doctest should be on this line).

        fpath (PathLike):
            Typically the same as modpath, only specified for non-python files
            (e.g. rst files).

        block_type (str | None):
            Hint indicating the type of docstring block. Can be ('Example',
            'Doctest', 'Script', 'Benchmark', 'zero-arg', etc..).

        mode (str):
            Hint at what created / is running this doctest. This impacts
            how results are presented and what doctests are skipped.
            Can be "native" or "pytest". Defaults to "pytest".

        config (DoctestConfig):
            configuration for running / checking the doctest

        module (ModuleType | None):
            a reference to the module that contains the doctest

        modname (str):
            name of the module that contains the doctest.

        failed_tb_lineno (int | None):
            Line number a failure occurred on.

        exc_info (None | tuple[type[BaseException], BaseException, types.TracebackType] | tuple[None, None, None]):
            traceback of a failure if one occurred.

        failed_part (None | DoctestPart):
            the part containing the failure if one occurred.

        warn_list (list):
            from :func:`warnings.catch_warnings`

        logged_evals (OrderedDict):
            Mapping from part index to what they evaluated to (if anything)

        logged_stdout (OrderedDict):
            Mapping from part index to captured stdout.

        global_namespace (dict):
            globals visible to the doctest

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

    # Attribute annotations derived from docstring
    module: types.ModuleType | None
    modname: str | None
    fpath: str | os.PathLike | None
    docsrc: str | None
    lineno: int | None
    num: int | None
    _parts: list['DoctestPart'] | None
    failed_tb_lineno: int | None
    exc_info: (
        tuple[type[BaseException], BaseException, types.TracebackType]
        | tuple[None, None, None]
        | None
    )
    failed_part: 'DoctestPart' | str | None
    warn_list: list | None
    _partfilename: str | None
    logged_evals: OrderedDict[int, typing.Any] | None
    logged_stdout: OrderedDict[int, str | None] | None
    _unmatched_stdout: list[str] | None
    _skipped_parts: list | None
    _runstate: typing.Any
    global_namespace: dict[str, typing.Any]

    # This is the doctest *part* that actually owns the traceback frame we
    # chose as the "interesting" frame for reporting. This is important for
    # doctests that define functions and fail in those functions.
    failed_tb_part: 'DoctestPart' | None

    # Internally we give each doctest part a synthetic file, this maps the name
    # back to the actual doctest part so we can correctly report traceback
    # frames in error reports
    _partfilename_to_part: dict[str, 'DoctestPart']

    def __init__(
        self,
        docsrc: str,
        modpath: str | os.PathLike | None = None,
        callname: str | None = None,
        num: int = 0,
        lineno: int = 1,
        fpath: str | os.PathLike | None = None,
        block_type: str | None = None,
        mode: str = 'pytest',
    ) -> None:
        """
        Args:
            docsrc (str): the text of the doctest
            modpath (str | PathLike | None):
            callname (str | None):
            num (int):
            lineno (int):
            fpath (str | None):
            block_type (str | None):
            mode (str):
        """
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
            self.modpath = getattr(
                self.module, '__file__', self.UNKNOWN_MODPATH
            )
        else:
            if fpath is not None:
                if fpath != modpath:
                    raise AssertionError(
                        'only specify fpath for non-python files'
                    )
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

        self._partfilename = None

        # stores the specific doctest part that owns the traceback frame that
        # we selected as the "user relevant" frame.
        self.failed_tb_part = None
        # Map synthetic per-part filenames back to the corresponding
        # DoctestPart.  This lets traceback rewriting recover the correct
        # source context even when a later part calls code defined in an
        # earlier part.
        self._partfilename_to_part = {}

        self.logged_evals = OrderedDict()
        self.logged_stdout = OrderedDict()
        self._unmatched_stdout = []
        self._skipped_parts = []

        self._runstate = None

        # Maintain global variables that this test will have access to
        self.global_namespace = {}
        # Hint at what is running this doctest
        self.mode = mode

    def __nice__(self) -> str:
        """
        Returns:
            str
        """
        parts: list[str] = []
        parts.append(str(self.modname))
        parts.append('%s:%s' % (self.callname, self.num))
        if self.lineno is not None:
            parts.append('ln %s' % (self.lineno))
        return ' '.join(parts)

    def __repr__(self) -> str:
        """
        Returns:
            str
        """
        classname = self.__class__.__name__
        devnice = self.__nice__()
        return '<%s(%s) at %s>' % (classname, devnice, hex(id(self)))

    def __str__(self) -> str:
        """
        Returns:
            str
        """
        classname = self.__class__.__name__
        devnice = self.__nice__()
        return '<%s(%s)>' % (classname, devnice)

    def is_disabled(self, pytest=False) -> bool:
        """
        Checks for comment directives on the first line of the doctest

        A doctest is force-disabled if it starts with any of the following
        patterns

        * ``>>> # DISABLE_DOCTEST``
        * ``>>> # SCRIPT``
        * ``>>> # UNSTABLE``
        * ``>>> # FAILING``

        And if running in pytest, you can also use

        * ``>>> import pytest; pytest.skip()``

        Note:
            modern versions of xdoctest contain directives like
            `# xdoctest: +SKIP`, which are a better way to do this.

        TODO:
            Robustly deprecate these non-standard ways of disabling a doctest.
            Generate a warning for several versions if they are used, and
            indicate what the replacement strategy is. Then raise an error for
            several more versions before finally removing this code.

        Returns:
            bool:
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
            disable_patterns += [r'>>>\s*#\s*pytest.skip']

        pattern = '|'.join(disable_patterns)
        assert self.docsrc is not None
        m = re.match(pattern, self.docsrc, flags=re.IGNORECASE)
        return m is not None

    @property
    def unique_callname(self) -> str:
        """
        A key that references this doctest given its module

        Returns:
            str
        """
        return f'{self.callname}:{self.num}'

    @property
    def node(self) -> str:
        """
        A key that references this doctest within pytest

        Returns:
            str
        """
        return f'{self.modpath}::{self.callname}:{self.num}'

    @property
    def valid_testnames(self) -> set[str]:
        """
        A set of callname and unique_callname

        Returns:
            Set[str]
        """
        return {
            self.callname,
            self.unique_callname,
        }

    def wants(self) -> typing.Generator[str, None, None]:
        """
        Returns a list of the populated wants

        Yields:
            str
        """
        self._parse()
        # _parse ensures _parts is a list
        assert self._parts is not None
        for part in self._parts:
            if part.want:
                yield part.want

    def format_parts(
        self,
        linenos: bool = True,
        colored: bool | None = None,
        want: bool = True,
        offset_linenos: bool | None = None,
        prefix: bool = True,
    ):
        """
        Used by :func:`format_src`

        Args:
            linenos (bool): show line numbers
            colored (bool | None): pygmentize the code
            want (bool): include the want value if it exists
            offset_linenos (bool): if True include the line offset relative to
                the source file
            prefix (bool): if False, exclude the doctest ``>>> `` prefix
        """
        self._parse()
        # ensure parts exists for subsequent loops
        assert self._parts is not None
        val = self.config.getvalue('colored', colored)
        if val is None:
            colored = False
        else:
            # allow ints or bools from config and coerce to bool
            colored = bool(val)
        partnos = self.config.getvalue('partnos')
        assert isinstance(partnos, bool)
        val2 = self.config.getvalue('offset_linenos', offset_linenos)
        if val2 is None:
            offset_linenos = None
        else:
            offset_linenos = bool(val2)

        n_digits = None
        startline = 1
        if linenos:
            if offset_linenos:
                assert self.lineno is not None
                startline = self.lineno
            n_lines = sum(p.n_lines for p in self._parts)
            endline = startline + n_lines

            n_digits_ = math.log(max(1, endline), 10)
            n_digits = int(math.ceil(n_digits_))

        for part in self._parts:
            part_text = part.format_part(
                linenos=linenos,
                want=want,
                startline=startline,
                n_digits=n_digits,
                prefix=prefix,
                colored=colored,
                partnos=partnos,
            )
            yield part_text

    def format_src(
        self,
        linenos: bool = True,
        colored: bool | None = None,
        want: bool = True,
        offset_linenos: bool | None = None,
        prefix: bool = True,
    ) -> str:
        """
        Adds prefix and line numbers to a doctest

        Args:
            linenos (bool): if True, adds line numbers to output

            colored (bool): if True highlight text with ansi colors. Default
                is specified in the config.

            want (bool): if True includes "want" lines (default False).

            offset_linenos (bool): if True offset line numbers to agree with
                their position in the source text file (default False).

            prefix (bool): if False, exclude the doctest ``>>> `` prefix

        Returns:
            str

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
        formated_parts = list(
            self.format_parts(
                linenos=linenos,
                colored=colored,
                want=want,
                offset_linenos=offset_linenos,
                prefix=prefix,
            )
        )
        full_source = '\n'.join(formated_parts)
        return full_source

    def _parse(self) -> None:
        """
        Divide the given string into examples and intervening text.

        Returns:
            None

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
            info = dict(
                callname=self.callname,
                modpath=self.modpath,
                lineno=self.lineno,
                fpath=self.fpath,
            )
            assert self.docsrc is not None
            raw_parts = parser.DoctestParser().parse(self.docsrc, info)
            # filter out strings that are inserted for text chunks
            self._parts = [p for p in raw_parts if not isinstance(p, str)]
        # Ensure part numbers are given
        assert self._parts is not None
        for partno, part in enumerate(self._parts):
            part.partno = partno

    def _import_module(self) -> None:
        """
        After this point we are in dynamic analysis mode, in most cases
        xdoctest should have been in static-analysis-only mode.

        Returns:
            None
        """
        if self.module is None:
            assert self.modname is not None
            if not self.modname.startswith('<'):
                # self.module = utils.import_module_from_path(self.modpath, index=0)
                if global_state.DEBUG_DOCTEST:
                    print('Pre-importing modpath = {}'.format(self.modpath))
                try:
                    # Note: there is a possibility of conflicts that arises
                    # here depending on your local environment. We may want to
                    # try and detect that.
                    assert self.modpath is not None
                    self.module = utils.import_module_from_path(
                        self.modpath, index=-1
                    )
                except RuntimeError as ex:
                    if global_state.DEBUG_DOCTEST:
                        print('sys.path={}'.format(sys.path))
                        print(
                            'Failed to pre-import modpath = {}'.format(
                                self.modpath
                            )
                        )
                    msg_parts = [
                        (
                            'XDoctest failed to pre-import the module '
                            'containing the doctest.'
                        )
                    ]
                    msg_parts.append(str(ex))
                    new_exc = RuntimeError('\n'.join(msg_parts))
                    if not self.config['supress_import_errors']:
                        raise
                    else:
                        # new_exc = ex
                        # Remove traceback before this line
                        new_exc.__traceback__ = None
                        # Backwards syntax compatible raise exc from None
                        # https://www.python.org/dev/peps/pep-3134/#explicit-exception-chaining
                        new_exc.__cause__ = None
                        raise new_exc
                else:
                    if global_state.DEBUG_DOCTEST:
                        print(
                            'Pre import success: self.module={}'.format(
                                self.module
                            )
                        )

    @staticmethod
    def _extract_future_flags(namespace: typing.Mapping) -> int:
        """
        Return the compiler-flags associated with the future features that
        have been imported into the given namespace (i.e. globals).

        Returns:
            int
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
            # Its unclear what the side effects of populating globals with
            # __name__, __package__, etc are. They do cause differences.
            # between that and IPython code. Probably regular code too.

            # https://stackoverflow.com/questions/32175693/python-importlibs-analogue-for-imp-new-module
            # https://stackoverflow.com/questions/31191947/pickle-and-exec-in-python
            # import types
            # dummy_name = self.module.__name__ + '_xdoctest_sandbox'
            # if dummy_name in sys.modules:
            #     dummy_mod = sys.modules[dummy_name]
            # else:
            # dummy_mod = types.ModuleType(dummy_name)
            # sys.modules[dummy_name] = dummy_mod

            test_globals.update(self.module.__dict__)
            # test_globals.update(dummy_mod.__dict__)
            # importable_attrs = {
            #     k: v for k, v in self.module.__dict__.items()
            #     if not k.startswith('__')
            # }
            # test_globals.update(importable_attrs)
            # test_globals['__name__'] = self.module.__name__ + '.doctest'
            # test_globals['__name__'] = '__main__'
            # test_globals['__file__'] = None
            # test_globals['__package__'] = None
            compileflags = self._extract_future_flags(test_globals)
        # force print function and division futures
        compileflags |= __future__.print_function.compiler_flag
        compileflags |= __future__.division.compiler_flag
        compileflags |= ast.PyCF_ALLOW_TOP_LEVEL_AWAIT
        return test_globals, compileflags

    def _partfilename_for(self, partno: int) -> str:
        """
        Construct a synthetic filename for a specific doctest part.

        We can't use one filename for the entire doctest because traceback
        frames only record a filename + line number. If every compiled part
        shares the same filename, then when a traceback points into code
        defined in an earlier part, we cannot tell which part that line number
        belongs to.

        Giving each part its own pseudo-filename makes traceback ownership
        unambiguous.
        """
        return f'<doctest:{self.node}:part{partno}>'

    def anything_ran(self) -> bool:
        """
        Returns:
            bool
        """
        # If everything was skipped, then there will be no stdout
        assert self.logged_stdout is not None
        return len(self.logged_stdout) > 0

    def _apply_module_doctest_metadata(
        self, runstate: directive.RuntimeState
    ) -> None:
        """
        Apply module-level doctestplus metadata to the current example.

        This is intentionally evaluated after the :class:`DocTest` already
        exists and has a callname, so the parser output shape stays unchanged.
        """
        skip_spec = None
        requires_spec = None

        if self.module is not None:
            skip_spec = getattr(self.module, '__doctest_skip__', None)
            requires_spec = getattr(self.module, '__doctest_requires__', None)
        else:
            modpath = self.modpath
            if isinstance(modpath, (str, os.PathLike)) and os.path.exists(
                modpath
            ):
                for key in ['__doctest_skip__', '__doctest_requires__']:
                    try:
                        value = static.parse_static_value(
                            key, fpath=os.fspath(modpath)
                        )
                    except NameError:
                        value = None
                    except Exception as ex:
                        raise ValueError(
                            'Failed to read {!r} from {!r}: {}'.format(
                                key, modpath, ex
                            )
                        )
                    if key == '__doctest_skip__':
                        skip_spec = value
                    else:
                        requires_spec = value

        if skip_spec is not None and self._matches_doctest_skip(skip_spec):
            runstate['SKIP'] = True
            return

        if requires_spec is not None and not self._module_requires_satisfied(
            requires_spec
        ):
            runstate['SKIP'] = True

    def _matches_doctest_skip(self, skip_spec: Any) -> bool:
        if isinstance(skip_spec, str):
            patterns = [skip_spec]
        elif isinstance(skip_spec, (list, tuple, set)):
            patterns = list(skip_spec)
        else:
            raise ValueError(
                '__doctest_skip__ must be a string or sequence of strings'
            )

        for pattern in patterns:
            if not isinstance(pattern, str):
                raise ValueError(
                    '__doctest_skip__ patterns must be strings, got {!r}'.format(
                        pattern
                    )
                )
            if pattern == '.':
                pattern = '__doc__'
            if fnmatch(self.callname, pattern):
                return True
        return False

    def _module_requires_satisfied(self, requires_spec: Any) -> bool:
        if not isinstance(requires_spec, dict):
            raise ValueError(
                '__doctest_requires__ must be a dictionary of patterns to requirements'
            )

        for key, reqs in requires_spec.items():
            if isinstance(key, str):
                patterns = [key]
            elif isinstance(key, (list, tuple, set)):
                patterns = list(key)
            else:
                raise ValueError(
                    '__doctest_requires__ keys must be strings or sequences of strings'
                )

            if not any(
                fnmatch(self.callname, pattern if pattern != '.' else '__doc__')
                for pattern in patterns
            ):
                continue
            if isinstance(reqs, str):
                req_list = [reqs]
            elif isinstance(reqs, (list, tuple, set)):
                req_list = list(reqs)
            else:
                raise ValueError(
                    '__doctest_requires__ values must be strings or sequences of strings'
                )

            for req_text in req_list:
                if not isinstance(req_text, str):
                    raise ValueError(
                        '__doctest_requires__ requirements must be strings'
                    )
                if not _doctest_requirement_satisfied(req_text):
                    return False

        return True

    def run(
        self, verbose: int | None | bool = None, on_error: str | None = None
    ) -> dict[str, typing.Any]:
        """
        Executes the doctest, checks the results, reports the outcome.

        Args:
            verbose (int): verbosity level
            on_error (str): can be 'raise' or 'return'

        Returns:
            Dict : summary
        """
        on_error = cast(
            Union[str, None], self.config.getvalue('on_error', on_error)
        )
        verbose = cast(int, self.config.getvalue('verbose', verbose))
        assert isinstance(verbose, int)
        if on_error not in {'raise', 'return'}:
            raise KeyError(on_error)

        self._parse()  # parse out parts if we have not already done so
        self._pre_run(verbose)

        # Prepare for actual test run
        assert self.logged_evals is not None
        assert self.logged_stdout is not None
        self.logged_evals.clear()
        self.logged_stdout.clear()
        self._unmatched_stdout = []

        self._skipped_parts = []
        self.exc_info = None
        self._suppressed_stdout = verbose <= 1

        # Reset traceback bookkeeping from any prior run.
        self.failed_tb_lineno = None
        self.failed_tb_part = None

        # Reset the synthetic filename bookkeeping for this run.
        self._partfilename = None
        self._partfilename_to_part = {}

        # Initialize a new runtime state
        default_state = self.config['default_runtime_state']
        runstate = self._runstate = directive.RuntimeState(default_state)
        # setup reporting choice
        runstate.set_report_style(self.config['reportchoice'].lower())

        # Defer the execution of the pre-import until we know at least one part
        # in the doctest will run.
        did_pre_import = False

        # Can't do this because we can't force execution of SCRIPTS
        # if self.is_disabled():
        #     runstate['SKIP'] = True

        needs_capture = True
        asyncio_runner = None
        is_running_in_loop = utils.util_asyncio.running()

        DEBUG = global_state.DEBUG_DOCTEST

        # Use the same capture object for all parts in the test
        cap = utils.CaptureStdout(
            suppress=self._suppressed_stdout, enabled=needs_capture
        )

        # NOTE: this will prevent any custom handling of warnings
        # See: https://github.com/Erotemic/xdoctest/issues/169
        with warnings.catch_warnings(record=True) as self.warn_list:
            assert self._parts is not None
            for partx, part in enumerate(self._parts):
                if DEBUG:
                    print(f'part[{partx}] checking')

                # Prepare to capture stdout and evaluated values
                self.failed_part = part  # Assume part will fail (it may not)
                got_eval = constants.NOT_EVALED

                # Extract directives and and update runtime state
                part_directive = part.directives
                if DEBUG:
                    print(f'part[{partx}] directives: {part_directive}')
                try:
                    try:
                        runstate.update(part_directive)
                    except Exception as ex:
                        assert self.lineno is not None
                        msg = 'Failed to parse directive: {} in {} at line {}. Caused by {}'.format(
                            part_directive,
                            self.fpath,
                            self.lineno + part.line_offset,
                            repr(ex),
                        )
                        raise Exception(msg)
                except Exception:
                    self.exc_info = sys.exc_info()
                    self.failed_tb_lineno = 1  # is this the directive line?
                    if on_error == 'raise':
                        raise
                    break

                if DEBUG:
                    print(f'part[{partx}] runstate={runstate}')
                    print(f'runstate._inline_state={runstate._inline_state}')
                    print(f'runstate._global_state={runstate._global_state}')

                # Handle runtime actions
                requires = runstate['REQUIRES']
                if runstate['SKIP'] or (
                    isinstance(requires, set) and len(requires) > 0
                ):
                    if DEBUG:
                        print(f'part[{partx}] runstate requests skipping')
                    self._skipped_parts.append(part)
                    continue

                if not part.has_any_code():
                    if DEBUG:
                        print(f'part[{partx}] No code, skipping')
                    self._skipped_parts.append(part)
                    continue

                if not did_pre_import:
                    # Execute the pre-import before the first run of
                    # non-skipped code.
                    if DEBUG:
                        print(f'part[{partx}] Importing parent module')
                    try:
                        self._import_module()
                    except Exception:
                        self.failed_part = '<IMPORT>'
                        self._partfilename = f'<doctest:{self.node}:pre_import>'
                        self.exc_info = sys.exc_info()
                        if on_error == 'raise':
                            raise
                        else:
                            summary = self._post_run(verbose)
                            return summary

                    self._apply_module_doctest_metadata(runstate)

                    if runstate['SKIP']:
                        if DEBUG:
                            print(f'part[{partx}] skipped by module metadata')
                        self._skipped_parts.append(part)
                        did_pre_import = True
                        continue

                    test_globals, compileflags = self._test_globals()

                    if DEBUG:
                        print(
                            'Global names = {}'.format(
                                sorted(test_globals.keys())
                            )
                        )

                    global_exec = self.config.getvalue('global_exec')
                    if global_exec:
                        # Hack to make it easier to specify multi-line input on the CLI
                        assert isinstance(global_exec, str)
                        global_source = utils.codeblock(
                            global_exec.replace('\\n', '\n')
                        )
                        global_code = compile(
                            global_source,
                            mode='exec',
                            filename=f'<doctest:{self.node}:global_exec>',
                            flags=compileflags,
                            dont_inherit=True,
                        )
                        exec(global_code, test_globals)

                    did_pre_import = True

                try:
                    # Give every doctest part its own synthetic filename.
                    #
                    # This matters because the traceback only tells us
                    # "filename X, line Y".
                    #
                    # Before this patch, every part in the doctest used the
                    # same filename, so when an exception happened inside a
                    # function defined earlier and called later, the traceback
                    # line number was ambiguous. xdoctest would later assume
                    # the traceback belonged to `self.failed_part`, which is
                    # often just the *calling* part, not the part that
                    # originally defined the code frame.
                    #
                    # By using a unique filename per part, traceback frames can
                    # be mapped back to the exact DoctestPart that owns them.
                    self._partfilename = self._partfilename_for(partx)

                    # Record the owning part so traceback rewriting can recover
                    # the correct part from the synthetic filename later.
                    self._partfilename_to_part[self._partfilename] = part

                    source_text = part.compilable_source()

                    # Compile code, handle syntax errors
                    #   part.compile_mode can be single, exec, or eval.
                    #   Typically single is used instead of eval
                    code = compile(
                        source_text,
                        mode=part.compile_mode,
                        filename=self._partfilename,
                        flags=compileflags,
                        dont_inherit=True,
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
                    try:
                        # close the asyncio runner (context exit)
                        if asyncio_runner is not None and not runstate['ASYNC']:
                            try:
                                asyncio_runner.close()
                            finally:
                                asyncio_runner = None
                        # Execute the doctest code
                        try:
                            # NOTE: For code passed to eval or exec, there is no
                            # difference between locals and globals. Only pass in
                            # one dict, otherwise there is weird behavior
                            with cap:
                                # We can execute each part using exec or eval.  If
                                # a doctest part has `compile_mode=eval` we
                                # expect it to return an object with a repr that
                                # can compared to a "want" statement.
                                # print('part.compile_mode = {!r}'.format(part.compile_mode))
                                is_coroutine = (
                                    code.co_flags & CO_COROUTINE == CO_COROUTINE
                                )
                                if is_coroutine or runstate['ASYNC']:
                                    if is_running_in_loop:
                                        raise exceptions.ExistingEventLoopError(
                                            'Cannot run async doctests from within a running event loop: %s',
                                            part.orig_lines,
                                        )
                                    if asyncio_runner is None:
                                        asyncio_runner = (
                                            utils.util_asyncio.Runner()
                                        )

                                    async def corofunc():
                                        if is_coroutine:
                                            return await eval(
                                                code, test_globals
                                            )
                                        else:
                                            return eval(code, test_globals)

                                    if part.compile_mode == 'eval':
                                        got_eval = asyncio_runner.run(
                                            corofunc()
                                        )
                                    else:
                                        asyncio_runner.run(corofunc())
                                else:
                                    if part.compile_mode == 'eval':
                                        got_eval = eval(code, test_globals)
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
                                exc_got = traceback.format_exception_only(
                                    *exception[:2]
                                )[-1]
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
                            self._check_or_defer_part_output(
                                part,
                                cap.text,
                                got_eval,
                                runstate,
                            )
                    except BaseException:
                        # close the asyncio runner (base exception)
                        if asyncio_runner is not None:
                            try:
                                asyncio_runner.close()
                            finally:
                                asyncio_runner = None
                        raise
                    else:
                        # close the asyncio runner (top-level await)
                        if asyncio_runner is not None and not runstate['ASYNC']:
                            try:
                                asyncio_runner.close()
                            finally:
                                asyncio_runner = None

                # Handle anything that could go wrong
                except KeyboardInterrupt:  # nocover
                    raise
                except (
                    exceptions.ExitTestException,
                    exceptions.Skipped,
                ) as ex:
                    if verbose > 0:
                        print('Test gracefully exists on: ex={}'.format(ex))
                    break
                except exceptions.ExistingEventLoopError:
                    # When we try to run a doctest with await, but there is
                    # already a running event loop.
                    self.exc_info = sys.exc_info()
                    if on_error == 'raise':
                        raise
                    break
                except checker.GotWantException:
                    # When the "got", doesn't match the "want"
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
                    ex_type, ex_value, tb = _exec_info = sys.exc_info()

                    DEBUG = global_state.DEBUG_DOCTEST
                    if DEBUG:
                        print('_ex_dbg = {!r}'.format(_ex_dbg))
                        print(
                            '<DEBUG: doctest encountered exception>',
                            file=sys.stderr,
                        )
                        print(''.join(traceback.format_tb(tb)), file=sys.stderr)
                        print('</DEBUG>', file=sys.stderr)

                    # Search for the traceback that corresponds with the
                    # doctest, and remove the parts that point to
                    # boilerplate lines in this file.
                    found_lineno = None
                    found_tb_part = None

                    # Walk the traceback looking for the first frame that came
                    # from one of our synthetic doctest-part filenames.
                    #
                    # We intentionally do NOT compare only against
                    # `self._partfilename` here.
                    #
                    # `self._partfilename` is just the filename of the part we
                    # most recently compiled / executed. But the traceback may
                    # point into code defined in an *earlier* part, for example
                    # a function or class method defined earlier and invoked by
                    # the current part.
                    #
                    # Therefore we resolve traceback ownership against the full
                    # `_partfilename_to_part` map for this run.
                    found_lineno = None
                    found_tb_part = None
                    found_sub_tb = None
                    for sub_tb in _traverse_traceback(tb):
                        tb_filename = sub_tb.tb_frame.f_code.co_filename
                        tb_part = self._partfilename_to_part.get(
                            tb_filename, None
                        )
                        if tb_part is not None:
                            # Walk up the traceback until we find the one that
                            # has the doctest as the base filename
                            found_lineno = sub_tb.tb_lineno
                            found_tb_part = tb_part
                            found_sub_tb = sub_tb

                    if DEBUG:
                        # The only traceback remaining should be
                        # the part that is relevant to the user
                        print('<DEBUG: best sub_tb>', file=sys.stderr)
                        print(
                            'found_lineno = {!r}'.format(found_lineno),
                            file=sys.stderr,
                        )
                        print(
                            'found_tb_part = {!r}'.format(found_tb_part),
                            file=sys.stderr,
                        )
                        print(
                            ''.join(traceback.format_tb(sub_tb)),
                            file=sys.stderr,
                        )
                        if found_sub_tb is not None:
                            print(
                                ''.join(traceback.format_tb(found_sub_tb)),
                                file=sys.stderr,
                            )
                        print('</DEBUG>', file=sys.stderr)

                    if found_lineno is None:
                        if DEBUG:
                            print(
                                'UNABLE TO CLEAN TRACEBACK. EXIT DUE TO DEBUG'
                            )
                            sys.exit(1)
                        raise ValueError(
                            f'Could not clean traceback: ex = {_ex_dbg!r}'
                        )
                    else:
                        # Store both the traceback-relative line number and the
                        # part that owns that traceback frame.
                        #
                        # Storing only the line number is not enough; later
                        # formatting code also needs to know which part's
                        # `orig_lines` or `exec_lines` should be used.
                        self.failed_tb_lineno = found_lineno
                        self.failed_tb_part = found_tb_part

                    self.exc_info = _exec_info

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

            # close the asyncio runner (no exception)
            if asyncio_runner is not None:
                try:
                    asyncio_runner.close()
                finally:
                    asyncio_runner = None

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

    def _check_or_defer_part_output(
        self,
        part: 'DoctestPart',
        got_stdout: str | None,
        got_eval: Any,
        runstate: directive.RuntimeState,
    ) -> None:
        """
        Apply the configured output contract for one executed part.

        With the default configuration, parts without a local want may defer
        stdout for later trailing matching, while parts with a local want are
        checked immediately. The `deferred_output_matching` knob disables the
        deferred-trailing behavior, and `optional_want` requires output
        producing parts to have a local want unless `IGNORE_WANT` or
        `IGNORE_OUTPUT` is active. Any part with either directive active is
        treated as a boundary and does not contribute output to later
        matching.
        """
        deferred_output_matching = bool(
            self.config.getvalue('deferred_output_matching')
        )
        optional_want = bool(self.config.getvalue('optional_want'))
        ignore_want = bool(runstate['IGNORE_WANT'])
        ignore_output = bool(runstate['IGNORE_OUTPUT'])

        if part.want is None:
            if ignore_output:
                self._unmatched_stdout = []
                return

            if ignore_want:
                self._unmatched_stdout = []
                return

            has_stdout = bool(got_stdout)
            has_eval = got_eval is not constants.NOT_EVALED
            if not optional_want and (has_stdout or has_eval):
                if has_stdout:
                    assert got_stdout is not None
                    got = got_stdout
                else:
                    try:
                        got = repr(got_eval)
                    except Exception as ex:
                        raise checker.ExtractGotReprException(
                            'Error calling repr for {}. Caused by: {!r}'.format(
                                type(got_eval), ex
                            ),
                            ex,
                        )
                raise checker.GotWantException(
                    'got output with no local want',
                    got,
                    '',
                )

            if deferred_output_matching and has_stdout:
                assert got_stdout is not None
                assert self._unmatched_stdout is not None
                self._unmatched_stdout.append(got_stdout)
        else:
            assert got_stdout is not None
            if not ignore_want and not ignore_output:
                part.check(
                    got_stdout,
                    got_eval,
                    runstate,
                    unmatched=self._unmatched_stdout,
                )
            # Any want-bearing part is a boundary for deferred stdout, even when
            # IGNORE_WANT / IGNORE_OUTPUT skip local comparison.
            self._unmatched_stdout = []

    @property
    def globs(self):
        """
        Alias for ``global_namespace`` for pytest 8.0 compatibility
        """
        return self.global_namespace

    @property
    def cmdline(self) -> str:
        """
        A cli-instruction that can be used to execute *this* doctest.

        Returns:
            str:
        """
        if self.mode == 'pytest':
            return 'pytest ' + self.node
        elif self.mode == 'native':
            return f'python -m xdoctest {self.modpath} {self.unique_callname}'
        else:
            raise KeyError(self.mode)

    @property
    def _block_prefix(self):
        return 'ZERO-ARG' if self.block_type == 'zero-arg' else 'DOCTEST'

    def _pre_run(self, verbose: bool | int) -> None:
        if verbose >= 1:
            if verbose >= 2:
                barrier = self._color('====== <exec> ======', 'white')
                print(barrier)
            if self.block_type == 'zero-arg':
                # zero-arg funcs arent doctests, but we can still run them
                print('* ZERO-ARG FUNC : {}'.format(self.node))
            else:
                print(
                    '* DOCTEST : {}, line {}'.format(self.node, self.lineno)
                    + self._color(' <- wrt source file', 'white')
                )
            if verbose >= 3:
                print(self._color(self._block_prefix + ' SOURCE', 'white'))
                print(self.format_src())
                print(
                    self._color(self._block_prefix + ' STDOUT/STDERR', 'white')
                )

    def failed_line_offset(self) -> int | None:
        """
        Determine which line in the doctest failed.
        """
        if self.exc_info is None:
            return None
        else:
            if self.failed_part == '<IMPORT>':
                return 0

            ex_type, ex_value, tb = self.exc_info
            assert self.failed_part is not None
            assert not isinstance(self.failed_part, str)

            if isinstance(
                ex_value,
                (
                    checker.ExtractGotReprException,
                    exceptions.ExistingEventLoopError,
                ),
            ):
                # These exceptions conceptually belong to the currently failed
                # part, not some nested traceback frame in earlier code.
                offset = self.failed_part.line_offset
                offset += self.failed_part.n_exec_lines

            elif isinstance(ex_value, checker.GotWantException):
                # Same idea here: got/want failures are about the currently
                # failed part's want block.
                offset = self.failed_part.line_offset
                offset += self.failed_part.n_exec_lines
                if self.failed_part.want is not None:
                    offset += 1

            else:
                # For ordinary execution exceptions, the relevant line may be
                # inside code defined by an earlier doctest part.
                assert self.failed_tb_lineno is not None
                tb_part = self.failed_tb_part or self.failed_part
                offset = tb_part.line_offset
                offset += self.failed_tb_lineno

            offset -= 1
            return offset

    def failed_lineno(self) -> int | None:
        """
        Returns:
            int | None
        """
        offset = self.failed_line_offset()
        if offset is None:
            return None
        else:
            # Find the first line of the part
            assert self.lineno is not None
            lineno = self.lineno + offset
            return lineno

    def repr_failure(self, with_tb: typing.Any = True) -> list[str]:
        r"""
        Constructs lines detailing information about a failed doctest

        Args:
            with_tb (bool): if True include the traceback

        Returns:
            List[str]

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
        #     lines += failed_part.exec_lines
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
        assert ex_type is not None
        assert fail_offset is not None
        lines = [
            f'* REASON: {ex_type.__name__}',
            self._color(self._block_prefix + ' DEBUG INFO', 'white'),
            f'  XDoc "{self.node}", line {fail_offset + 1}'
            + self._color(' <- wrt doctest', 'red'),
        ]

        colored = self.config['colored']
        if fail_lineno is not None:
            fpath = self.UNKNOWN_FPATH if self.fpath is None else self.fpath
            lines += [
                '  File "{}", line {},'.format(fpath, fail_lineno)
                + self._color(' <- wrt source file', 'red')
            ]

        # lines += ['  in doctest "{}", line {}'.format(self.unique_callname,
        #                                               fail_offset + 1) +
        #           self._color(' <- relative line number in the docstest', 'red')]

        # source_text = self.format_src(colored=colored, linenos=True,
        #                               want=False)
        # source_text = utils.indent(source_text)
        # lines += source_text.splitlines()

        def r1_strip_nl(text: str | None) -> str | None:
            if text is None:
                return None
            return text[:-1] if text.endswith('\n') else text

        # if self.logged_stdout:
        #     lines += ['stdout results:']
        #     lines += [r1_strip_nl(t) for t in self.logged_stdout.values() if t]

        textgen = self.format_parts(colored=colored, linenos=True, want=False)

        n_digits = 1

        # Logic to break output between pass, failed, and unexecuted parts
        before_part_lines: list[str] = []
        fail_part_lines: list[str] = []
        after_parts_lines: list[str] = []
        temp = [before_part_lines, fail_part_lines, after_parts_lines]
        tindex = 0
        indent_text = ' ' * (5 + n_digits)

        assert self._parts is not None
        assert self._skipped_parts is not None
        assert self.logged_stdout is not None
        assert ex_value is not None

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
            assert hasattr(ex_value, 'output_repr_difference')
            # Cast to GotWantException since we verified it has the required methods
            ex_value_cast = typing.cast(checker.GotWantException, ex_value)
            lines += [
                ex_value_cast.output_difference(
                    self._runstate, colored=colored
                ),
                ex_value_cast.output_repr_difference(self._runstate),
            ]
        else:
            if with_tb:
                # TODO: enhance formatting to show an IPython-like output of
                # where the error occurred in the doctest
                tblines = traceback.format_exception(*self.exc_info)

                def _alter_traceback_linenos(
                    self, tblines: list[str]
                ) -> list[str]:
                    def overwrite_lineno(
                        linepart: list[str],
                        tb_part: 'DoctestPart',
                        tb_lineno: int,
                    ) -> list[str]:
                        """
                        Rewrite the displayed traceback line number so it
                        refers to the user's doctest line numbers instead of
                        the synthetic per-part filename's local line numbers.

                        `tb_lineno` is local to `tb_part`.
                        We convert it to:
                            - `rel_lineno`: line relative to the full doctest
                            - `abs_lineno`: line relative to the original source file
                        """
                        rel_lineno = tb_part.line_offset + tb_lineno
                        abs_lineno = self.lineno + rel_lineno - 1

                        new_linestr = f'rel: {rel_lineno}, abs: {abs_lineno}'
                        linepart = linepart[:-1] + [new_linestr]
                        return linepart

                    def lookup_tb_part(
                        line,
                    ) -> tuple[None, None] | tuple[str, 'DoctestPart']:
                        """
                        Given a traceback text line, find which synthetic
                        per-part filename it refers to and then recover the
                        owning DoctestPart.

                        We sort by descending filename length as a small
                        robustness measure in case one synthetic filename could
                        ever be a substring of another.
                        """
                        _fname_to_part: dict[str, 'DoctestPart'] = (
                            self._partfilename_to_part
                        )
                        if not _fname_to_part:
                            return None, None

                        partfilename_list: list[str] = sorted(
                            _fname_to_part.keys(), key=str.__len__, reverse=True
                        )
                        for partfilename in partfilename_list:
                            if partfilename in line:
                                part = self._partfilename_to_part[partfilename]
                                return partfilename, part

                        return None, None

                    def lookup_ctx_line(tb_part, tb_lineno):
                        """
                        Recover the source context line to append after the
                        traceback frame.

                        `orig_lines` is formatter-oriented and may not always
                        be present.  It is nice when available because it
                        preserves the original doctest prompt formatting.

                        `orig_lines`. Compared to previous versions this fixes
                        ownership, and only then use a small, defensive
                        fallback to `exec_lines` if needed.
                        """
                        ctx_lines = (
                            tb_part.orig_lines or tb_part.exec_lines or []
                        )
                        if 1 <= tb_lineno <= len(ctx_lines):
                            return ctx_lines[tb_lineno - 1]
                        return ''

                    new_tblines = []
                    for i, line in enumerate(tblines):
                        matched_filename, tb_part = lookup_tb_part(line)

                        if matched_filename is not None and tb_part is not None:
                            # Example input line shape:
                            #   File "<doctest:...:part0>", line 2, in foo
                            #
                            # We parse the local traceback line number, then rewrite it to
                            # doctest-relative / source-relative numbers.
                            tbparts = line.split(',')
                            tb_lineno = int(tbparts[-2].strip().split()[1])

                            linepart = tbparts[-2].split(' ')
                            linepart = overwrite_lineno(
                                linepart, tb_part, tb_lineno
                            )
                            tbparts[-2] = ' '.join(linepart)
                            new_line = ','.join(tbparts)

                            # We now fetch the context line from the part that actually owns the
                            # traceback frame, not from `self.failed_part`.
                            #
                            # This is the direct fix for the IndexError class of bugs that occur
                            # when the traceback points into an earlier definition part.
                            failed_ctx = lookup_ctx_line(tb_part, tb_lineno)
                            extra = ('    ' + failed_ctx) if failed_ctx else ''
                            line = new_line + extra + '\n'

                        new_tblines.append(line)

                    return new_tblines

                new_tblines = _alter_traceback_linenos(self, tblines)

                if colored:
                    tbtext = '\n'.join(new_tblines)
                    tbtext = utils.highlight_code(
                        tbtext, lexer_name='pytb', stripall=True
                    )
                    new_tblines = tbtext.splitlines()
                lines += new_tblines

        lines += [self._color(self._block_prefix + ' REPRODUCTION', 'white')]
        lines += ['CommandLine:']
        lines += ['    ' + self.cmdline]
        return lines

    def _print_captured(self) -> None:
        assert self.logged_stdout is not None
        out_text = ''.join([v for v in self.logged_stdout.values() if v])
        if out_text is not None:
            assert isinstance(out_text, str), 'do not use bytes'
        try:
            print(out_text)
        except UnicodeEncodeError:
            print('Weird travis bug')
            print('type(out_text) = %r' % (type(out_text),))
            print('out_text = %r' % (out_text,))

    def _color(self, text: str, color: str, enabled: bool | None = None):
        """conditionally color text based on config and flags"""
        colored = self.config.getvalue('colored', enabled)
        if colored:
            text = utils.color_text(text, color)
        return text

    def _post_run(self, verbose: bool | int) -> dict[str, typing.Any]:
        """
        Returns:
            Dict : summary
        """
        # print('POST RUN verbose = {!r}'.format(verbose))
        assert self._skipped_parts is not None
        assert self._parts is not None

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
    # nested function with free variable.  Not sure how necessary this is
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

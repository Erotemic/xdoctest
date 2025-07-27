"""
The Pytest XDoctest Plugin
--------------------------

This file is registered as a pytest plugin when you install xdoctest. By
executing pytest with ``--xdoctest-modules`` (or simply ``--xdoctest``), this
plugin will be enabled. This also disables the original builtin doctest plugin.

When xdoctest is enabled, pytest will discover and run doctests in modules and
test files using xdoctest's improved parser and runtime environment.

To ensure maximum backwards compatibility with the original doctest module,
this code is heavilly based on ``pytest/_pytest/doctest.py`` plugin file in
https://github.com/pytest-dev/pytest

"""
from importlib import import_module
from inspect import getmembers
from typing import Union
import pytest
from _pytest._code import code
from _pytest import fixtures

try:
    from packaging.version import parse as Version
except ImportError:  # nocover
    from distutils.version import LooseVersion as Version

_PYTEST_IS_GE_620 = Version(pytest.__version__) >= Version('6.2.0')
_PYTEST_IS_GE_800 = Version(pytest.__version__) >= Version('8.0.0')


if _PYTEST_IS_GE_800:
    from typing import Dict
    from _pytest.fixtures import TopRequest


# def print(text):
#     """ Hack so we can get stdout when debugging the plugin file """
#     import os
#     fpath = os.path.expanduser('~/plugin.stdout.txt')
#     with open(fpath, 'a') as file:
#         file.write(str(text) + '\n')

__docstubs__ = """
import xdoctest.doctest_example
"""


def monkey_patch_disable_normal_doctest():
    """
    The doctest plugin captures tests even if it is disabled. This causes
    conflicts with this package. Thus, we monkey-patch ``_pytest.doctest`` to
    prevent it from collecting anything. Perhaps there is a less terrible way
    to do this.

    Note:
        * Legacy and deprecated function.
        * The monkey-patching of `_pytest.doctest` is destructive --
          the original values of the overwritten attributes are not
          preserved nor restored.
    """
    # XXX: should we delete this outright?
    import sys
    from _pytest import doctest
    # Only perform the monkey patch if it is clear the xdoctest plugin is
    # wanted instead of the standard _pytest.doctest pluginn
    if '--doctest-modules' not in sys.argv:
        if '--xdoctest-modules' in sys.argv or '--xdoctest' in sys.argv or '--xdoc' in sys.argv:
            # overwriting the collect function will cripple _pytest.doctest and
            # prevent conflicts with this module.
            def pytest_collect_file(path, parent):
                return None
            # Not sure why, but _is_doctest seems to be called even when
            # pytest_collect_file is monkey patched out
            def _is_doctest(config, path, parent):
                return False
            doctest.pytest_collect_file = pytest_collect_file
            doctest._is_doctest = _is_doctest


def pytest_configure(config):
    def get_dunder(obj, attr: str) -> Union[str, None]:
        try:
            module = obj.__module__
        except AttributeError:
            return None
        if isinstance(module, str) and module:
            return module
        return None

    # XXX: should we simplify `plugin_uses_xdoctest()`?

    def plugin_uses_xdoctest(plugin) -> bool:
        # Check the `.__[qual]name__` of plugin where available
        for attr in '__qualname__', '__name__':
            name = get_dunder(plugin, attr)
            if not name:
                continue
            if 'xdoctest' in name:
                return True
        # Check the module defining `plugin` (if a class, function,
        # etc.)
        module = get_dunder(plugin, '__module__')
        if module:
            if 'xdoctest' in module:
                return True
            try:
                if plugin_uses_xdoctest(import_module(module)):
                    return True
            except (ValueError, ImportError):
                pass
        # Finally, check the module of all the object members
        try:
            member_modules = {get_dunder(value, '__module__')
                              for _, value in getmembers(plugin)}
        except Exception:
            member_modules = set()
        return any('xdoctest' in module for module in member_modules - {None})

    manager = config.pluginmanager
    all_plugins = {manager.get_name(plugin): plugin
                   for plugin in manager.get_plugins()}
    doctest_plugins = {name: plugin for name, plugin in all_plugins.items()
                       if 'doctest' in name}
    # Are we using `xdoctest`? If not, unregister this plugin
    if not getattr(config.option, 'xdoctestmodules', False):
        if 'xdoctest' in doctest_plugins:
            manager.unregister(doctest_plugins['xdoctest'])
        return
    # If yes, unregister all the doctest-related plugins which don't
    # have to do with `xdoctest`
    for name, plugin in doctest_plugins.items():
        if not plugin_uses_xdoctest(plugin):
            manager.unregister(plugin)


def pytest_addoption(parser):
    # TODO: make this programmatically mirror the argparse in __main__
    from xdoctest import core

    def str_lower(x):
        # python2 fix
        return str.lower(str(x))

    group = parser.getgroup('collect')
    parser.addini('xdoctest_encoding', 'encoding used for xdoctest files', default='utf-8')
    # parser.addini('xdoctest_options', 'default directive flags for doctests',
    #               type="args", default=["+ELLIPSIS"])
    group.addoption('--xdoctest-modules', '--xdoctest', '--xdoc',
                    action='store_true', default=False,
                    help='Run doctests in all .py modules using new style parsing',
                    dest='xdoctestmodules')
    group.addoption('--xdoctest-glob', '--xdoc-glob',
                    action='append', default=[], metavar='pat',
                    help=(
                        'Text files matching this pattern will be checked '
                        'for doctests. This option may be specified multiple '
                        'times. XDoctest does not check any text files by '
                        'default. For compatibility with doctest set this to '
                        'test*.txt'),
                    dest='xdoctestglob')
    group.addoption('--xdoctest-ignore-syntax-errors',
                    action='store_true', default=False,
                    help='Ignore xdoctest SyntaxErrors',
                    dest='xdoctest_ignore_syntax_errors')

    group.addoption('--xdoctest-style', '--xdoc-style',
                    type=str_lower, default='freeform',
                    help='Basic style used to write doctests',
                    choices=core.DOCTEST_STYLES,
                    dest='xdoctest_style')

    group.addoption('--xdoctest-analysis', '--xdoc-analysis',
                    type=str_lower, default='auto',
                    help=('How doctests are collected. '
                          'Can either be static, dynamic, or auto'),
                    choices=['static', 'dynamic', 'auto'],
                    dest='xdoctest_analysis')

    from xdoctest import doctest_example
    doctest_example.DoctestConfig()._update_argparse_cli(
        group.addoption, prefix=['xdoctest', 'xdoc'],
        defaults=dict(verbose=2)
    )


if pytest.__version__ < '7.':  # nocover
    def pytest_collect_file(path, parent):
        return _pytest_collect_file(path, parent, fspath=path)

    def _suffix(path):
        return path.ext

    def _match(path, glob):
        return path.check(fnmatch=glob)

else:
    def pytest_collect_file(file_path, parent):  # type: ignore
        return _pytest_collect_file(file_path, parent, path=file_path)

    def _suffix(path):
        return path.suffix

    def _match(path, glob):
        return path.match(glob)


def _pytest_collect_file(file_path, parent, **path_args):
    config = parent.config
    if _suffix(file_path) == ".py":
        if config.option.xdoctestmodules:
            if hasattr(XDoctestModule, 'from_parent'):
                return XDoctestModule.from_parent(parent, **path_args)
            else:
                return XDoctestModule(file_path, parent)
    elif _is_xdoctest(config, file_path, parent):
        if hasattr(XDoctestTextfile, 'from_parent'):
            return XDoctestTextfile.from_parent(parent, **path_args)
        else:
            return XDoctestTextfile(file_path, parent)


def _is_xdoctest(config, path, parent):
    matched = False
    if _suffix(path) in ('.txt', '.rst') and parent.session.isinitpath(path):
        matched = True
    else:
        globs = config.getoption("xdoctestglob")
        for glob in globs:
            if _match(path, glob):
                matched = True
                break
    return matched


class ReprFailXDoctest(code.TerminalRepr):

    def __init__(self, reprlocation, lines):
        """
        Args:
            reprlocation (Any):
                _pytest._code.code.ReprFileLocation where the error happened
            lines (List[str]): text of the error
        """
        self.reprlocation = reprlocation
        self.lines = lines

    def toterminal(self, tw):
        for line in self.lines:
            tw.line(line)
        self.reprlocation.toterminal(tw)


class XDoctestItem(pytest.Item):
    def __init__(self,
                 name,
                 parent,
                 runner=None,
                 dtest=None):
        """
        Args:
            name (str):
            parent (Any | None):
            dtest (xdoctest.doctest_example.DocTest):
        """
        super(XDoctestItem, self).__init__(name, parent)
        self.cls = XDoctestItem
        self.dtest = dtest
        self.obj = None
        if _PYTEST_IS_GE_800:
            # Stuff needed for fixture support in pytest > 8.0.
            fm = self.session._fixturemanager
            fixtureinfo = fm.getfixtureinfo(node=self, func=None, cls=None)
            self._fixtureinfo = fixtureinfo
            self.fixturenames = fixtureinfo.names_closure
            self._initrequest()
        else:
            self.fixture_request = None

    if _PYTEST_IS_GE_800:
        @classmethod
        def from_parent(  # type: ignore
            cls,
            parent,
            name,
            runner=None,
            dtest=None,
        ):
            # incompatible signature due to imposed limits on subclass
            """The public named constructor."""
            return super().from_parent(name=name, parent=parent, runner=runner, dtest=dtest)

    @property
    def example(self):
        """
        Backwards compatability with older pytest versions
        """
        return self.dtest

    def _initrequest(self) -> None:
        assert _PYTEST_IS_GE_800
        self.funcargs: Dict[str, object] = {}
        self._request = TopRequest(self, _ispytest=True)  # type: ignore[arg-type]

    def setup(self):
        if _PYTEST_IS_GE_800:
            self._request._fillfixtures()
            globs = dict(getfixture=self._request.getfixturevalue)
            for name, value in self._request.getfixturevalue("xdoctest_namespace").items():
                globs[name] = value
            self.dtest.globs.update(globs)
        else:
            if self.dtest is not None:
                self.fixture_request = _setup_fixtures(self)
                global_namespace = dict(getfixture=self.fixture_request.getfixturevalue)
                for name, value in self.fixture_request.getfixturevalue('xdoctest_namespace').items():
                    global_namespace[name] = value
                self.dtest.global_namespace.update(global_namespace)

    def runtest(self):
        if self.dtest.is_disabled(pytest=True):
            pytest.skip('doctest encountered global skip directive')
        # verbose = self.dtest.config['verbose']
        self.dtest.run(on_error='raise')
        if not self.dtest.anything_ran():
            pytest.skip('doctest is empty or all parts were skipped')

    def repr_failure(self, excinfo):
        """
        # Args:
        #     excinfo (_pytest._code.code.ExceptionInfo):

        # Returns:
        #     ReprFailXDoctest | str | _pytest._code.code.TerminalRepr:
        """
        dtest = self.dtest
        if dtest.exc_info is not None:
            lineno = dtest.failed_lineno()
            type = dtest.exc_info[0]
            message = type.__name__
            reprlocation = code.ReprFileLocation(dtest.fpath, lineno, message)
            lines = dtest.repr_failure()

            return ReprFailXDoctest(reprlocation, lines)
        else:
            return super(XDoctestItem, self).repr_failure(excinfo)

    def reportinfo(self):
        """
        Returns:
            Tuple[str, int, str]
        """
        return self.fspath, self.dtest.lineno, "[xdoctest] %s" % self.name


class _XDoctestBase(pytest.Module):

    def _prepare_internal_config(self):

        class NamespaceLike:
            def __init__(self, config):
                self.config = config
            def __getitem__(self, attr):
                return self.config.getvalue('xdoctest_' + attr)
            def __getattr__(self, attr):
                return self.config.getvalue('xdoctest_' + attr)

        ns = NamespaceLike(self.config)

        from xdoctest import doctest_example
        self._examp_conf = doctest_example.DoctestConfig()._populate_from_cli(ns)


class XDoctestTextfile(_XDoctestBase):
    obj = None

    def collect(self):
        """
        Yields:
            XDoctestItem
        """
        from xdoctest import core
        encoding = self.config.getini("xdoctest_encoding")
        text = self.fspath.read_text(encoding)
        filename = str(self.fspath)
        name = self.fspath.basename
        global_namespace = {'__name__': '__main__'}

        self._prepare_internal_config()

        style = self.config.getvalue('xdoctest_style')

        _example_iter = core.parse_docstr_examples(
            text, name, fpath=filename, style=style)

        for dtest in _example_iter:
            dtest.global_namespace.update(global_namespace)
            dtest.config.update(self._examp_conf)
            if hasattr(XDoctestItem, 'from_parent'):
                yield XDoctestItem.from_parent(
                    self, name=name, dtest=dtest)
            else:
                # direct construction is deprecated
                yield XDoctestItem(name, self, dtest=dtest)


class XDoctestModule(_XDoctestBase):
    def collect(self):
        from xdoctest import core
        modpath = str(self.fspath)

        style = self.config.getvalue('xdoctest_style')
        analysis = self.config.getvalue('xdoctest_analysis')
        self._prepare_internal_config()

        try:
            examples = list(core.parse_doctestables(modpath, style=style,
                                                    analysis=analysis))
        except SyntaxError:
            if self.config.getvalue('xdoctest_ignore_syntax_errors'):
                pytest.skip('unable to import module %r' % self.fspath)
            else:
                raise

        for dtest in examples:
            dtest.config.update(self._examp_conf)
            name = dtest.unique_callname
            if hasattr(XDoctestItem, 'from_parent'):
                yield XDoctestItem.from_parent(
                    self, name=name, dtest=dtest)
            else:
                # direct construction is deprecated
                yield XDoctestItem(name, self, dtest=dtest)


def _setup_fixtures(xdoctest_item):
    """
    Used by XDoctestTextfile and XDoctestItem to setup fixture information.

    Args:
        xdoctest_item (XDoctestItem):

    Returns:
        fixtures.FixtureRequest
    """
    def func():
        pass

    xdoctest_item.funcargs = {}
    fm = xdoctest_item.session._fixturemanager
    xdoctest_item._fixtureinfo = fm.getfixtureinfo(
        node=xdoctest_item, func=func, cls=None, funcargs=False)
    # Note: FixtureRequest may change in the future, we are using
    # private functionality. Hopefully it wont break, but we should
    # check to see if there is a better way to do this
    # https://github.com/pytest-dev/pytest/discussions/8512#discussioncomment-563347
    if _PYTEST_IS_GE_620:
        # The "_ispytest" arg was added in 3.6.1
        fixture_request = fixtures.FixtureRequest(xdoctest_item, _ispytest=True)
    else:
        fixture_request = fixtures.FixtureRequest(xdoctest_item)
    fixture_request._fillfixtures()
    return fixture_request


@pytest.fixture(scope='session')
def xdoctest_namespace():
    """
    Inject names into the xdoctest namespace.

    Returns:
        Dict
    """
    return dict()

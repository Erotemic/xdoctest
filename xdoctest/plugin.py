# -*- coding: utf-8 -*-
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
from __future__ import absolute_import, division, print_function
import pytest
from _pytest._code import code
from _pytest import fixtures
from distutils.version import LooseVersion
# import traceback


# def print(text):
#     """ Hack so we can get stdout when debugging the plugin file """
#     import os
#     fpath = os.path.expanduser('~/plugin.stdout.txt')
#     with open(fpath, 'a') as file:
#         file.write(str(text) + '\n')


### WE SHALL NOW BE VERY NAUGHTY ###
def monkey_patch_disable_normal_doctest():
    """
    The doctest plugin captures tests even if it is disabled. This causes
    conflicts with this package. Thus, we monkey-patch ``_pytest.doctest`` to
    prevent it from collecting anything. Perhaps there is a less terrible way
    to do this.
    """
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


monkey_patch_disable_normal_doctest()
### THE NAUGHTINESS MUST NOW CEASE ###


def pytest_addoption(parser):
    # TODO: make this programatically mirror the argparse in __main__
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
                    help='run doctests in all .py modules using new style parsing',
                    dest='xdoctestmodules')
    group.addoption('--xdoctest-glob', '--xdoc-glob',
                    action='append', default=[], metavar='pat',
                    help=(
                        'text files matching this pattern will be checked '
                        'for doctests. This option may be specified multiple '
                        'times. XDoctest does not check any text files by '
                        'default. For compatibility with doctest set this to '
                        'test*.txt'),
                    dest='xdoctestglob')
    group.addoption('--xdoctest-ignore-syntax-errors',
                    action='store_true', default=False,
                    help='ignore xdoctest SyntaxErrors',
                    dest='xdoctest_ignore_syntax_errors')

    group.addoption('--xdoctest-style', '--xdoc-style',
                    type=str_lower, default='freeform',
                    help='basic style used to write doctests',
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
        defaults=dict(verbose=0)
    )


def pytest_collect_file(path, parent):
    config = parent.config
    if path.ext == ".py":
        if config.option.xdoctestmodules:
            if hasattr(XDoctestModule, 'from_parent'):
                return XDoctestModule.from_parent(parent, fspath=path)
            else:
                return XDoctestModule(path, parent)
    elif _is_xdoctest(config, path, parent):
        if hasattr(XDoctestTextfile, 'from_parent'):
            return XDoctestTextfile.from_parent(parent, fspath=path)
        else:
            return XDoctestTextfile(path, parent)


def _is_xdoctest(config, path, parent):
    matched = False
    if path.ext in ('.txt', '.rst') and parent.session.isinitpath(path):
        matched = True
    else:
        globs = config.getoption("xdoctestglob")
        for glob in globs:
            if path.check(fnmatch=glob):
                matched = True
                break
    return matched


class ReprFailXDoctest(code.TerminalRepr):

    def __init__(self, reprlocation, lines):
        self.reprlocation = reprlocation
        self.lines = lines

    def toterminal(self, tw):
        for line in self.lines:
            tw.line(line)
        self.reprlocation.toterminal(tw)


class XDoctestItem(pytest.Item):
    def __init__(self, name, parent, example=None):
        super(XDoctestItem, self).__init__(name, parent)
        self.cls = XDoctestItem
        self.example = example
        self.obj = None
        self.fixture_request = None

    def setup(self):
        if self.example is not None:
            self.fixture_request = _setup_fixtures(self)
            global_namespace = dict(getfixture=self.fixture_request.getfixturevalue)
            for name, value in self.fixture_request.getfixturevalue('xdoctest_namespace').items():
                global_namespace[name] = value
            self.example.global_namespace.update(global_namespace)

    def runtest(self):
        if self.example.is_disabled(pytest=True):
            pytest.skip('doctest encountered global skip directive')
        # verbose = self.example.config['verbose']
        self.example.run(on_error='raise')
        if not self.example.anything_ran():
            pytest.skip('doctest is empty or all parts were skipped')

    def repr_failure(self, excinfo):
        example = self.example
        if example.exc_info is not None:
            lineno = example.failed_lineno()
            type = example.exc_info[0]
            message = type.__name__
            reprlocation = code.ReprFileLocation(example.fpath, lineno, message)
            lines = example.repr_failure()

            return ReprFailXDoctest(reprlocation, lines)
        else:
            return super(XDoctestItem, self).repr_failure(excinfo)

    def reportinfo(self):
        return self.fspath, self.example.lineno, "[xdoctest] %s" % self.name


class _XDoctestBase(pytest.Module):

    def _prepare_internal_config(self):

        class NamespaceLike(object):
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

        for example in _example_iter:
            example.global_namespace.update(global_namespace)
            example.config.update(self._examp_conf)
            if hasattr(XDoctestItem, 'from_parent'):
                yield XDoctestItem.from_parent(
                    self, name=name, example=example)
            else:
                # direct construction is deprecated
                yield XDoctestItem(name, self, example)


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

        for example in examples:
            example.config.update(self._examp_conf)
            name = example.unique_callname
            if hasattr(XDoctestItem, 'from_parent'):
                yield XDoctestItem.from_parent(
                    self, name=name, example=example)
            else:
                # direct construction is deprecated
                yield XDoctestItem(name, self, example)


_PYTEST_IS_GE_620 = LooseVersion(pytest.__version__) >= LooseVersion('6.2.0')
# _PYTEST_IS_GE_620 = 0


def _setup_fixtures(xdoctest_item):
    """
    Used by XDoctestTextfile and XDoctestItem to setup fixture information.
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
    """
    return dict()

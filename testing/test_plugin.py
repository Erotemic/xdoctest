# encoding: utf-8
"""
Adapted from the original `pytest/testing/test_doctest.py` module at:
    https://github.com/pytest-dev/pytest
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import _pytest._code
from _pytest.compat import MODULE_NOT_FOUND_ERROR
from xdoctest.plugin import XDoctestItem, XDoctestModule, XDoctestTextfile
from xdoctest import utils
import pytest

EXTRA_ARGS = ['-p', 'pytester', '-p', 'no:doctest', '--xdoctest-nocolor']


def explicit_testdir():
    r"""
    Explicitly constructs a testdir for use in IPython development
    Note used by any tests.

    # https://xr.gs/2017/07/pytest-dynamic-runtime-fixtures-python3/
    https://stackoverflow.com/questions/45970572/how-to-get-a-pytest-fixture-interactively

    Ignore:
        python -c codeblock "
        from __future__ import absolute_import, division, print_function
        import subprocess, grp
        import imp, inspect, textwrap, pprint, json, tempfile, string, lzma, bz2, shutil
        import glob, time, struct, bisect, pdb, platform, atexit, shlex,
        import sys
        s1 = set(sys.modules)
        import pytest
        s2 = set(sys.modules)
        print('\n'.join(sorted(s2 - s1)))
        "
    """
    # modpath = _modname_to_modpath_backup('pytest')
    # import pytest  # NOQA
    # import sys
    # if 'pytest' in sys.modules:
    #     for k in list(sys.modules):
    #         if k.startswith(('_pytest.', 'py.')):
    #             del sys.modules[k]
    #         elif k in {'_pytest', 'py'}:
    #             del sys.modules[k]
    # import _pytest
    # import _pytest.config
    # import _pytest.main
    # import _pytest.tmpdir
    # import _pytest.fixtures
    # import _pytest.runner
    # import _pytest.python
    # _pytest.config._preloadplugins()  # to populate pytest.* namespace so help(pytest) works
    import _pytest
    config = _pytest.config._prepareconfig(['-s'], plugins=['pytester'])
    session = _pytest.main.Session(config)

    _pytest.tmpdir.pytest_configure(config)
    _pytest.fixtures.pytest_sessionstart(session)
    _pytest.runner.pytest_sessionstart(session)

    def func(testdir):
        pass

    parent = _pytest.python.Module('parent', config=config, session=session)
    function = _pytest.python.Function(
        'func', parent, callobj=func, config=config, session=session)
    _pytest.fixtures.fillfixtures(function)
    testdir = function.funcargs['testdir']

    # from _pytest.compat import _setup_collect_fakemodule
    # _setup_collect_fakemodule()
    return testdir


def _modname_to_modpath_backup(modname):
    """
    Alternative version that does not rely on pkgutil, which is broken when
    using pytest. This only does very basic module lookup.
    """
    from os.path import join, isfile, exists
    import sys
    candidate_fnames = [
        join(modname, '.py'),
        join(modname, '.pyc'),
        join(modname, '.pyo'),
        # join(modname, '.so'),  # TODO: dylib pyd
    ]
    modname = modname.replace('.', '/')
    candidate_dpaths = ['.'] + sys.path
    for dpath in candidate_dpaths:
        for fname in candidate_fnames:
            # Check for file-based modules
            modpath = join(dpath, fname)
            if isfile(modpath):
                return modpath
            # Check for directory-based modules
            modpath = join(dpath, modname)
            if exists(modpath):
                if isfile(join(modpath, '__init__.py')):
                    return modpath
            # Check for egg-links
            egglink = join(dpath, modname + '.egg-link')
            if exists(egglink):
                with open(egglink, 'r') as f:
                    modpath = f.readline().strip()
                if isfile(join(modpath, '__init__.py')):
                    return modpath
            # Check for easy-install
            # easyinstall = join(dpath, 'easy-install.pth')
            # if exists(easyinstall):
            #     pass
            #     # with open(easyinstall, 'r') as f:
            #     #     candidate_dpaths.extend(f.readlines())
            #     # TODO easyinstall checks


class TestXDoctest(object):

    def test_collect_testtextfile(self, testdir):
        """
        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_collect_testtextfile
        """
        w = testdir.maketxtfile(whatever="")
        checkfile = testdir.maketxtfile(test_something="""
            alskdjalsdk
            >>> i = 5
            >>> i-1
            4
        """)

        for x in (testdir.tmpdir, checkfile):
            items, reprec = testdir.inline_genitems(x, *EXTRA_ARGS)
            assert len(items) == 1
            assert isinstance(items[0], XDoctestItem)
            assert isinstance(items[0].parent, XDoctestTextfile)
        # Empty file has no items.
        items, reprec = testdir.inline_genitems(w)
        assert len(items) == 0

    def test_collect_module_empty(self, testdir):
        """
        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_collect_module_empty
        """
        path = testdir.makepyfile(whatever="#")
        for p in (path, testdir.tmpdir):
            items, reprec = testdir.inline_genitems(p,
                                                    '--xdoctest-modules')
            assert len(items) == 0

    def test_simple_doctestfile(self, testdir):
        """
        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_simple_doctestfile

        Ignore:
            >>> import sys
            >>> sys.path.append('/home/joncrall/code/xdoctest/testing')
            >>> from test_plugin import *
            >>> testdir = explicit_testdir()
        """
        p = testdir.maketxtfile(test_doc="""
            >>> x = 1
            >>> x == 1
            False
        """)
        reprec = testdir.inline_run(p, *EXTRA_ARGS)
        reprec.assertoutcome(failed=1)

    def test_new_pattern(self, testdir):
        """
        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_new_pattern
        """
        p = testdir.maketxtfile(xdoc="""
            >>> x = 1
            >>> x == 1
            False
        """)
        reprec = testdir.inline_run(p, "--xdoctest-glob=x*.txt", *EXTRA_ARGS)
        reprec.assertoutcome(failed=1)

    def test_multiple_patterns(self, testdir):
        """Test support for multiple --xdoctest-glob arguments (#1255).

        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_multiple_patterns
        """
        testdir.maketxtfile(xdoc="""
            >>> 1
            1
        """)
        testdir.makefile('.foo', test="""
            >>> 1
            1
        """)
        testdir.maketxtfile(test_normal="""
            >>> 1
            1
        """)
        expected = set(['xdoc.txt', 'test.foo', 'test_normal.txt'])
        assert set(x.basename for x in testdir.tmpdir.listdir()) == expected
        args = ["--xdoctest-glob=xdoc*.txt", "--xdoctest-glob=*.foo"]
        result = testdir.runpytest(*args + EXTRA_ARGS)
        result.stdout.fnmatch_lines([
            '*test.foo *',
            '*xdoc.txt *',
            '*2 passed*',
        ])
        result = testdir.runpytest(*EXTRA_ARGS)
        result.stdout.fnmatch_lines([
            '*test_normal.txt *',
            '*1 passed*',
        ])

    @pytest.mark.parametrize(
        '   test_string,    encoding',
        [
            (u'foo', 'ascii'),
            (u'öäü', 'latin1'),
            (u'öäü', 'utf-8')
        ]
    )
    def test_encoding(self, testdir, test_string, encoding):
        """Test support for xdoctest_encoding ini option.

        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_encoding
        """
        testdir.makeini("""
            [pytest]
            xdoctest_encoding={0}
        """.format(encoding))
        xdoctest = u"""
            >>> u"{0}"
            {1}
        """.format(test_string, repr(test_string))
        testdir._makefile(".txt", [xdoctest], {}, encoding=encoding)

        result = testdir.runpytest(*EXTRA_ARGS)

        result.stdout.fnmatch_lines([
            '*1 passed*',
        ])

    def test_doctest_unexpected_exception(self, testdir):
        """
        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_doctest_unexpected_exception

        Ignore:
            >>> import sys
            >>> sys.path.append('/home/joncrall/code/xdoctest/testing')
            >>> from test_plugin import *
            >>> testdir = explicit_testdir()
            >>> self = TestXDoctest()
            >>> self.test_doctest_unexpected_exception(testdir)
        """
        # import sys
        # try:
        #     i = 0
        #     0 / i
        # except Exception as ex:
        #     exc_info = sys.exc_info()
        # import traceback
        # traceback.format_exception(*exc_info)

        testdir.maketxtfile("""
            >>> i = 0
            >>> 0 / i
            2
        """)
        result = testdir.runpytest("--xdoctest-modules")
        # print('<stdout>')
        # print('\n'.join(result.stdout.lines))
        # print('</stdout>')

        result.stdout.fnmatch_lines([
            "*FAILED DOCTEST*",
            "*>>> i = 0*",
            "*>>> 0 / i*",
        ])

        # result.stdout.fnmatch_lines([
        #     "*unexpected_exception*",
        #     "*>>> i = 0*",
        #     "*>>> 0 / i*",
        #     "*FAILED*ZeroDivision*",
        # ])

    def test_doctest_property_lineno(self, testdir):
        """
        REPLACES: test_doctest_linedata_missing
        REASON: Static parsing means we do know this line number.

        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_doctest_property_lineno
        """
        testdir.tmpdir.join('hello.py').write(_pytest._code.Source(utils.codeblock(
            """
            class Fun(object):
                @property
                def test(self):
                    '''
                    >>> a = 1
                    >>> 1 / 0
                    '''
            """)))
        result = testdir.runpytest("--xdoctest-modules", *EXTRA_ARGS)
        result.stdout.fnmatch_lines([
            "*FAILED DOCTEST: ZeroDivisionError*",
            '*on line 6*',
            '*on line 2*',
            "*1 >>> a = 1*",
            "*2 >>> 1 / 0*",
            "*ZeroDivision*",
            "*1 failed*",
        ])

    def test_docstring_show_entire_doctest(self, testdir):
        """Test that we show the entire doctest when there is a failure

        REPLACES: test_docstring_context_around_error
        REPLACES: test_docstring_context_around_error

        # XDOCTEST DOES NOT SHOW NON-SOURCE CONTEXT

        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_docstring_show_entire_doctest
        """
        testdir.makepyfile(utils.codeblock(
            '''
            def foo():
                """
                Example:
                    >>> x = 4
                    >>> x = 5 + x
                    >>> x = 6 + x
                    >>> x = 7 + x
                    >>> x
                    22
                    >>> x = 8 + x
                    >>> x = 9 + x
                    >>> x = 10 + x
                    >>> x = 11 + x
                    >>> x = 12 + x
                    >>> x
                    42

                text-line-after
                """
            '''))
        result = testdir.runpytest('--xdoctest-modules', *EXTRA_ARGS)
        result.stdout.fnmatch_lines([
            '*FAILED*',
            '* 1 >>> x = 4*',
            '* 2 >>> x = 5 + x*',
            '* 3 >>> x = 6 + x*',
            '* 4 >>> x = 7 + x*',
            '* 5 >>> x*',
            '* 7 >>> x = 8 + x*',
            '* 8 >>> x = 9 + x*',
            '* 9 >>> x = 10 + x*',
            '*10 >>> x = 11 + x*',
            '*11 >>> x = 12 + x*',
            '*12 >>> x*',
            'Expected:',
            '    42',
            'Got:',
            '    72',
        ])
        # non-source lines should be trimmed out
        assert 'Example:' not in result.stdout.str()
        assert 'text-line-after' not in result.stdout.str()

    def test_doctest_unex_importerror_only_txt(self, testdir):
        """
        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_doctest_unex_importerror_only_txt
        """
        testdir.maketxtfile("""
            >>> import asdalsdkjaslkdjasd
        """)
        result = testdir.runpytest(*EXTRA_ARGS)
        # xdoctest is never executed because of error during hello.py collection
        result.stdout.fnmatch_lines([
            '*FAILED*',
            "*>>> import asdals*",
            "*{e}: No module named *asdal*".format(e=MODULE_NOT_FOUND_ERROR),
        ])

    def test_doctest_unex_importerror_with_module(self, testdir):
        """
        CHANGES:
            No longer fails durring collection because we're doing
            static-parsing baby!

        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_doctest_unex_importerror_with_module
        """
        testdir.tmpdir.join("hello.py").write(_pytest._code.Source("""
            import asdalsdkjaslkdjasd
        """))
        testdir.maketxtfile("""
            >>> import hello
        """)
        # because python is not started from this dir, it cant find the hello
        # module in the temporary dir without adding it to the path
        import os
        import sys
        cwd = os.getcwd()
        sys.path.append(cwd)
        result = testdir.runpytest("--xdoctest-modules", "-s", *EXTRA_ARGS)
        result.stdout.fnmatch_lines([
            '*FAILED*',
            '*1 >>> import hello*',
            "*{e}: No module named *asdals*".format(e=MODULE_NOT_FOUND_ERROR),
            # "*Interrupted: 1 errors during collection*",
        ])
        sys.path.pop()

    def test_doctestmodule_external_and_issue116(self, testdir):
        """
        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_doctestmodule_external_and_issue116
        """
        p = testdir.mkpydir("hello")
        p.join("__init__.py").write(_pytest._code.Source("""
            def somefunc():
                '''
                    >>> i = 0
                    >>> i + 1
                    2
                '''
        """))
        result = testdir.runpytest(p, "--xdoctest-modules", *EXTRA_ARGS)
        result.stdout.fnmatch_lines([
            '*1 *>>> i = 0',
            '*2 *>>> i + 1',
            '*Expected:',
            "*    2",
            "*Got:",
            "*    1",
            "*:6: GotWantException"
        ])

    def test_txtfile_failing(self, testdir):
        """
        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_txtfile_failing
        """
        p = testdir.maketxtfile("""
            >>> i = 0
            >>> i + 1
            2
        """)
        result = testdir.runpytest(p, "-s", *EXTRA_ARGS)
        result.stdout.fnmatch_lines([
            '*1 >>> i = 0',
            '*2 >>> i + 1',
            'Expected:',
            "    2",
            "Got:",
            "    1",
            "*test_txtfile_failing.txt:3: GotWantException"
        ])

    def test_txtfile_with_fixtures(self, testdir):
        """
        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_txtfile_with_fixtures
        """
        p = testdir.maketxtfile("""
            >>> dir = getfixture('tmpdir')
            >>> type(dir).__name__
            'LocalPath'
        """)
        reprec = testdir.inline_run(p, *EXTRA_ARGS)
        reprec.assertoutcome(passed=1)

    def test_txtfile_with_usefixtures_in_ini(self, testdir):
        """
        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_txtfile_with_usefixtures_in_ini
        """
        testdir.makeini("""
            [pytest]
            usefixtures = myfixture
        """)
        testdir.makeconftest("""
            import pytest
            @pytest.fixture
            def myfixture(monkeypatch):
                monkeypatch.setenv("HELLO", "WORLD")
        """)

        p = testdir.maketxtfile("""
            >>> import os
            >>> os.environ["HELLO"]
            'WORLD'
        """)
        reprec = testdir.inline_run(p, *EXTRA_ARGS)
        reprec.assertoutcome(passed=1)

    def test_ignored_whitespace(self, testdir):
        testdir.makeini("""
            [pytest]
            doctest_optionflags = ELLIPSIS NORMALIZE_WHITESPACE
        """)
        p = testdir.makepyfile("""
            class MyClass(object):
                '''
                >>> a = "foo    "
                >>> print(a)
                foo
                '''
                pass
        """)
        reprec = testdir.inline_run(p, "--xdoctest-modules", *EXTRA_ARGS)
        reprec.assertoutcome(passed=1)

    def test_ignored_whitespace_glob(self, testdir):
        testdir.makeini("""
            [pytest]
            doctest_optionflags = ELLIPSIS NORMALIZE_WHITESPACE
        """)
        p = testdir.maketxtfile(xdoc="""
            >>> a = "foo    "
            >>> print(a)
            foo
        """)
        reprec = testdir.inline_run(p, "--xdoctest-glob=x*.txt", *EXTRA_ARGS)
        reprec.assertoutcome(passed=1)

    def test_contains_unicode(self, testdir):
        """Fix internal error with docstrings containing non-ascii characters.
        """
        testdir.makepyfile(u'''
            # encoding: utf-8
            def foo():
                """
                >>> name = 'с' # not letter 'c' but instead Cyrillic 's'.
                'anything'
                """
        ''')
        result = testdir.runpytest('--xdoctest-modules', *EXTRA_ARGS)
        result.stdout.fnmatch_lines([
            'Got nothing',
            '* 1 failed in*',
        ])

    def test_junit_report_for_doctest(self, testdir):
        """
        #713: Fix --junit-xml option when used with --xdoctest-modules.
        """
        p = testdir.makepyfile("""
            def foo():
                '''
                >>> 1 + 1
                3
                '''
                pass
        """)
        reprec = testdir.inline_run(p, "--xdoctest-modules",
                                    "--junit-xml=junit.xml")
        reprec.assertoutcome(failed=1)

    def test_unicode_doctest_module(self, testdir):
        """
        Test case for issue 2434: DecodeError on Python 2 when xdoctest docstring
        contains non-ascii characters.

        pytest -rsxX -p pytester testing/test_plugin.py::TestXDoctest::test_unicode_doctest_module

        """
        p = testdir.makepyfile(test_unicode_doctest_module="""
            # -*- encoding: utf-8 -*-
            from __future__ import unicode_literals

            def fix_bad_unicode(text):
                '''
                    >>> print(fix_bad_unicode('Ãºnico'))
                    único
                '''
                return "único"
        """)
        result = testdir.runpytest(p, '--xdoctest-modules', *EXTRA_ARGS)
        result.stdout.fnmatch_lines(['* 1 passed *'])

    def test_xdoctest_multiline_string(self, testdir):
        import textwrap
        p = testdir.maketxtfile(test_xdoctest_multiline_string=textwrap.dedent(
            """
            .. xdoctest::

                # Old way
                >>> print('''
                ... It would be nice if we didnt have to deal with prefixes
                ... in multiline strings.
                ... '''.strip())
                It would be nice if we didnt have to deal with prefixes
                in multiline strings.

                # New way
                >>> print('''
                    Multiline can now be written without prefixes.
                    Editing them is much more natural.
                    '''.strip())
                Multiline can now be written without prefixes.
                Editing them is much more natural.

                # This is ok too
                >>> print('''
                >>> Just prefix everything with >>> and the xdoctest should work
                >>> '''.strip())
                Just prefix everything with >>> and the xdoctest should work
            """).lstrip())
        result = testdir.runpytest(p, *EXTRA_ARGS)
        result.stdout.fnmatch_lines(['* 3 passed *'])

    def test_xdoctest_multiline_list(self, testdir):
        p = testdir.maketxtfile(test_xdoctest_multiline_string="""
            .. xdoctest::

                >>> x = [1, 2, 3,
                >>>      4, 5, 6]
                >>> print(len(x))
                6
        """)
        result = testdir.runpytest(p, *EXTRA_ARGS)
        result.stdout.fnmatch_lines(['* 1 passed *'])

    def test_xdoctest_trycatch(self, testdir):
        """
        CommandLine:
            pytest -rsxX -p pytester testing/test_plugin.py::TestXDoctest::test_xdoctest_trycatch
        """
        p = testdir.maketxtfile(test_xdoctest_multiline_string="""
            .. xdoctest::

                # Old way
                >>> try:
                ...     print('foo')
                ... except Exception as ex:
                ...     print('baz')
                ... else:
                ...     print('bar')
                foo
                bar

                # New way
                >>> try:
                >>>     print('foo')
                >>> except Exception as ex:
                >>>     print('baz')
                >>> else:
                >>>     print('bar')
                foo
                bar
        """)
        result = testdir.runpytest(p, *EXTRA_ARGS)
        result.stdout.fnmatch_lines(['* 2 passed *'])

    def test_xdoctest_functions(self, testdir):
        p = testdir.maketxtfile(test_xdoctest_multiline_string="""
            .. xdoctest::

                # Old way
                >>> def func():
                ...     print('we used to be slaves to regexes')
                >>> func()
                we used to be slaves to regexes

                # New way
                >>> def func():
                >>>     print('but now we can write code like humans')
                >>> func()
                but now we can write code like humans
        """)
        result = testdir.runpytest(p, *EXTRA_ARGS)
        result.stdout.fnmatch_lines(['* 2 passed *'])


class TestXDoctestModuleLevel(object):

    def test_doctestmodule(self, testdir):
        """
        CommandLine:
            pytest testing/test_plugin.py::TestXDoctestModuleLevel::test_doctestmodule

        Ignore:
            >>> import sys
            >>> sys.path.append('/home/joncrall/code/xdoctest/testing')
            >>> from test_plugin import *
            >>> testdir = explicit_testdir()
            >>> self = TestXDoctest()
        """
        p = testdir.makepyfile("""
            '''
                >>> x = 1
                >>> x == 1
                False

            '''
        """)
        reprec = testdir.inline_run(p, "--xdoctest-modules")
        # print(reprec.stdout.str())
        # print(reprec.listoutcomes())
        reprec.assertoutcome(failed=1)

    def test_collect_module_single_modulelevel_doctest(self, testdir):
        """
        CommandLine:
            pytest testing/test_plugin.py::TestXDoctestModuleLevel::test_collect_module_single_modulelevel_doctest

        Ignore:
            >>> import sys
            >>> sys.path.append('/home/joncrall/code/xdoctest/testing')
            >>> from test_plugin import *
            >>> testdir = explicit_testdir()
            >>> self = TestXDoctestModuleLevel()
        """
        path = testdir.makepyfile(whatever='""">>> pass"""')
        for p in (path, testdir.tmpdir):
            items, reprec = testdir.inline_genitems(p, '--xdoc', *EXTRA_ARGS)
            assert len(items) == 1
            assert isinstance(items[0], XDoctestItem)
            assert isinstance(items[0].parent, XDoctestModule)

    def test_collect_module_two_doctest_one_modulelevel(self, testdir):
        path = testdir.makepyfile(whatever="""
            '>>> x = None'
            def my_func():
                ">>> magic = 42 "
        """)
        for p in (path, testdir.tmpdir):
            items, reprec = testdir.inline_genitems(p, '--xdoc', *EXTRA_ARGS)
            assert len(items) == 2
            assert isinstance(items[0], XDoctestItem)
            assert isinstance(items[1], XDoctestItem)
            assert isinstance(items[0].parent, XDoctestModule)
            assert items[0].parent is items[1].parent

    def test_collect_module_two_doctest_no_modulelevel(self, testdir):
        """
        CommandLine:
            pytest testing/test_plugin.py::TestXDoctestModuleLevel::test_collect_module_two_doctest_no_modulelevel

        Ignore:
            >>> import sys
            >>> sys.path.append('/home/joncrall/code/xdoctest/testing')
            >>> from test_plugin import *
            >>> testdir = explicit_testdir()
            >>> self = TestXDoctestModuleLevel()
        """
        path = testdir.makepyfile(whatever="""
            '# Empty'
            def my_func():
                ">>> magic = 42 "
            def unuseful():
                '''
                # This is a function
                # >>> # it doesn't have any xdoctest
                '''
            def another():
                '''
                # This is another function
                >>> import os # this one does have a xdoctest
                '''
        """)
        for p in (path, testdir.tmpdir):
            items, reprec = testdir.inline_genitems(p, '--xdoc', *EXTRA_ARGS)
            print('reprec = {!r}'.format(reprec))
            print('items = {!r}'.format(items))
            assert len(items) == 2
            assert isinstance(items[0], XDoctestItem)
            assert isinstance(items[1], XDoctestItem)
            assert isinstance(items[0].parent, XDoctestModule)
            assert items[0].parent is items[1].parent


class TestLiterals(object):

    @pytest.mark.parametrize('config_mode', ['ini', 'comment'])
    @pytest.mark.skip('bytes are not supported yet')
    def test_allow_unicode(self, testdir, config_mode):
        """Test that doctests which output unicode work in all python versions
        tested by pytest when the ALLOW_UNICODE option is used (either in
        the ini file or by an inline comment).
        """
        if config_mode == 'ini':
            testdir.makeini('''
            [pytest]
            doctest_optionflags = ALLOW_UNICODE
            ''')
            comment = ''
        else:
            comment = '#xdoctest: +ALLOW_UNICODE'

        testdir.maketxtfile(test_doc="""
            >>> b'12'.decode('ascii') {comment}
            '12'
        """.format(comment=comment))
        testdir.makepyfile(foo="""
            def foo():
              '''
              >>> b'12'.decode('ascii') {comment}
              '12'
              '''
        """.format(comment=comment))
        reprec = testdir.inline_run("--xdoctest-modules", *EXTRA_ARGS)
        reprec.assertoutcome(passed=2)

    @pytest.mark.parametrize('config_mode', ['ini', 'comment'])
    @pytest.mark.skip('bytes are not supported yet')
    def test_allow_bytes(self, testdir, config_mode):
        """Test that doctests which output bytes work in all python versions
        tested by pytest when the ALLOW_BYTES option is used (either in
        the ini file or by an inline comment)(#1287).
        """
        if config_mode == 'ini':
            testdir.makeini('''
            [pytest]
            doctest_optionflags = ALLOW_BYTES
            ''')
            comment = ''
        else:
            comment = '#xdoctest: +ALLOW_BYTES'

        testdir.maketxtfile(test_doc="""
            >>> b'foo'  {comment}
            'foo'
        """.format(comment=comment))
        testdir.makepyfile(foo="""
            def foo():
              '''
              >>> b'foo'  {comment}
              'foo'
              '''
        """.format(comment=comment))
        reprec = testdir.inline_run("--xdoctest-modules")
        reprec.assertoutcome(passed=2)

    @pytest.mark.skip('bytes are not supported yet')
    def test_unicode_string(self, testdir):
        """Test that doctests which output unicode fail in Python 2 when
        the ALLOW_UNICODE option is not used. The same test should pass
        in Python 3.
        """
        testdir.maketxtfile(test_doc="""
            >>> b'12'.decode('ascii')
            '12'
        """)
        reprec = testdir.inline_run(*EXTRA_ARGS)
        passed = int(sys.version_info[0] >= 3)
        reprec.assertoutcome(passed=passed, failed=int(not passed))

    @pytest.mark.skip('bytes are not supported yet')
    def test_bytes_literal(self, testdir):
        """Test that doctests which output bytes fail in Python 3 when
        the ALLOW_BYTES option is not used. The same test should pass
        in Python 2 (#1287).
        """
        testdir.maketxtfile(test_doc="""
            >>> b'foo'
            'foo'
        """)
        reprec = testdir.inline_run()
        passed = int(sys.version_info[0] == 2)
        reprec.assertoutcome(passed=passed, failed=int(not passed))


class TestXDoctestSkips(object):
    """
    If all examples in a xdoctest are skipped due to the SKIP option, then
    the tests should be SKIPPED rather than PASSED. (#957)
    """

    def test_xdoctest_skips_diabled(self, testdir):
        testdir.makepyfile(foo="""
            import sys

            def foo():
                '''
                DisableDoctest:
                    >>> True
                    True
                '''
        """)
        result = testdir.runpytest("--xdoctest-modules", *EXTRA_ARGS)
        result.stdout.fnmatch_lines(['*no tests ran*'])

    @pytest.fixture(params=['text', 'module'])
    def makedoctest(self, testdir, request):
        def makeit(xdoctest):
            mode = request.param
            if mode == 'text':
                testdir.maketxtfile(xdoctest)
            else:
                assert mode == 'module'
                testdir.makepyfile('"""\n%s"""' % xdoctest)

        return makeit

    @pytest.mark.skip('we dont support the +SKIP directive')
    def test_one_skipped(self, testdir, makedoctest):
        makedoctest("""
            >>> 1 + 1  # xdoctest: +SKIP
            2
            >>> 2 + 2
            4
        """)
        reprec = testdir.inline_run("--xdoctest-modules")
        reprec.assertoutcome(passed=1)

    @pytest.mark.skip('we dont support the +SKIP directive')
    def test_one_skipped_failed(self, testdir, makedoctest):
        makedoctest("""
            >>> 1 + 1  # xdoctest: +SKIP
            2
            >>> 2 + 2
            200
        """)
        reprec = testdir.inline_run("--xdoctest-modules")
        reprec.assertoutcome(failed=1)

    @pytest.mark.skip('we dont support the +SKIP directive')
    def test_all_skipped(self, testdir, makedoctest):
        makedoctest("""
            >>> 1 + 1  # xdoctest: +SKIP
            2
            >>> 2 + 2  # xdoctest: +SKIP
            200
        """)
        reprec = testdir.inline_run("--xdoctest-modules")
        reprec.assertoutcome(skipped=1)

    def test_vacuous_all_skipped(self, testdir, makedoctest):
        makedoctest('')
        reprec = testdir.inline_run("--xdoctest-modules")
        reprec.assertoutcome(passed=0, skipped=0)


class TestXDoctestAutoUseFixtures(object):

    SCOPES = ['module', 'session', 'class', 'function']

    def test_doctest_module_session_fixture(self, testdir):
        """Test that session fixtures are initialized for xdoctest modules (#768)
        """
        # session fixture which changes some global data, which will
        # be accessed by doctests in a module
        testdir.makeconftest("""
            import pytest
            import sys

            @pytest.yield_fixture(autouse=True, scope='session')
            def myfixture():
                assert not hasattr(sys, 'pytest_session_data')
                sys.pytest_session_data = 1
                yield
                del sys.pytest_session_data
        """)
        testdir.makepyfile(foo="""
            import sys

            def foo():
              '''
              >>> assert sys.pytest_session_data == 1
              '''

            def bar():
              '''
              >>> assert sys.pytest_session_data == 1
              '''
        """)
        result = testdir.runpytest("--xdoctest-modules")
        result.stdout.fnmatch_lines(['*2 passed*'])

    @pytest.mark.parametrize('scope', SCOPES)
    @pytest.mark.parametrize('enable_doctest', [True, False])
    def test_fixture_scopes(self, testdir, scope, enable_doctest):
        """Test that auto-use fixtures work properly with xdoctest modules.
        See #1057 and #1100.
        """
        testdir.makeconftest('''
            import pytest

            @pytest.fixture(autouse=True, scope="{scope}")
            def auto(request):
                return 99
        '''.format(scope=scope))
        testdir.makepyfile(test_1='''
            def test_foo():
                """
                >>> getfixture('auto') + 1
                100
                """
            def test_bar():
                assert 1
        ''')
        params = ('--xdoctest-modules',) if enable_doctest else ()
        passes = 3 if enable_doctest else 2
        result = testdir.runpytest(*params)
        result.stdout.fnmatch_lines(['*=== %d passed in *' % passes])

    @pytest.mark.parametrize('scope', SCOPES)
    @pytest.mark.parametrize('autouse', [True, False])
    @pytest.mark.parametrize('use_fixture_in_doctest', [True, False])
    def test_fixture_module_doctest_scopes(self, testdir, scope, autouse,
                                           use_fixture_in_doctest):
        """Test that auto-use fixtures work properly with xdoctest files.
        See #1057 and #1100.
        """
        testdir.makeconftest('''
            import pytest

            @pytest.fixture(autouse={autouse}, scope="{scope}")
            def auto(request):
                return 99
        '''.format(scope=scope, autouse=autouse))
        if use_fixture_in_doctest:
            testdir.maketxtfile(test_doc="""
                >>> getfixture('auto')
                99
            """)
        else:
            testdir.maketxtfile(test_doc="""
                >>> 1 + 1
                2
            """)
        result = testdir.runpytest('--xdoctest-modules', *EXTRA_ARGS)
        assert 'FAILURES' not in str(result.stdout.str())
        result.stdout.fnmatch_lines(['*=== 1 passed in *'])

    @pytest.mark.parametrize('scope', SCOPES)
    def test_auto_use_request_attributes(self, testdir, scope):
        """Check that all attributes of a request in an autouse fixture
        behave as expected when requested for a xdoctest item.
        """
        testdir.makeconftest('''
            import pytest

            @pytest.fixture(autouse=True, scope="{scope}")
            def auto(request):
                if "{scope}" == 'module':
                    assert request.module is None
                if "{scope}" == 'class':
                    assert request.cls is None
                if "{scope}" == 'function':
                    assert request.function is None
                return 99
        '''.format(scope=scope))
        testdir.maketxtfile(test_doc="""
            >>> 1 + 1
            2
        """)
        result = testdir.runpytest('--xdoctest-modules', *EXTRA_ARGS)
        assert 'FAILURES' not in str(result.stdout.str())
        result.stdout.fnmatch_lines(['*=== 1 passed in *'])


@pytest.mark.skip
class TestXDoctestNamespaceFixture(object):
    """
    Not sure why these tests wont work

    pytest testing/test_plugin.py::TestXDoctestNamespaceFixture
    """

    SCOPES = ['module', 'session', 'class', 'function']

    @pytest.mark.parametrize('scope', SCOPES)
    def test_namespace_doctestfile(self, testdir, scope):
        """
        Check that inserting something into the namespace works in a
        simple text file xdoctest
        """
        testdir.makeconftest("""
            import pytest
            import contextlib

            @pytest.fixture(autouse=True, scope="{scope}")
            def add_contextlib(doctest_namespace):
                doctest_namespace['cl'] = contextlib
        """.format(scope=scope))
        p = testdir.maketxtfile("""
            >>> print(cl.__name__)
            contextlib
        """)
        reprec = testdir.inline_run(p)
        reprec.assertoutcome(passed=1)

    @pytest.mark.parametrize('scope', SCOPES)
    def test_namespace_pyfile(self, testdir, scope):
        """
        Check that inserting something into the namespace works in a
        simple Python file docstring xdoctest

        pytest testing/test_plugin.py::TestXDoctestNamespaceFixture::test_namespace_pyfile
        """
        testdir.makeconftest("""
            import pytest
            import contextlib

            @pytest.fixture(autouse=True, scope="{scope}")
            def add_contextlib(doctest_namespace):
                doctest_namespace['cl'] = contextlib
        """.format(scope=scope))
        p = testdir.makepyfile("""
            def foo():
                '''
                >>> print(cl.__name__)
                contextlib
                '''
        """)
        reprec = testdir.inline_run(p, "--xdoctest-modules")
        reprec.assertoutcome(passed=1)


class TestXDoctestReportingOption(object):
    @pytest.mark.skip
    def _run_doctest_report(self, testdir, format):
        testdir.makepyfile("""
            def foo():
                '''
                >>> foo()
                   a  b
                0  1  4
                1  2  4
                2  3  6
                '''
                print('   a  b\\n'
                      '0  1  4\\n'
                      '1  2  5\\n'
                      '2  3  6')
            """)
        return testdir.runpytest("--xdoctest-modules", "--xdoctest-report", format)

    @pytest.mark.parametrize('format', ['udiff', 'UDIFF', 'uDiFf'])
    @pytest.mark.skip
    def test_doctest_report_udiff(self, testdir, format):
        result = self._run_doctest_report(testdir, format)
        result.stdout.fnmatch_lines([
            '     0  1  4',
            '    -1  2  4',
            '    +1  2  5',
            '     2  3  6',
        ])

    @pytest.mark.skip
    def test_doctest_report_cdiff(self, testdir):
        result = self._run_doctest_report(testdir, 'cdiff')
        result.stdout.fnmatch_lines([
            '         a  b',
            '      0  1  4',
            '    ! 1  2  4',
            '      2  3  6',
            '    --- 1,4 ----',
            '         a  b',
            '      0  1  4',
            '    ! 1  2  5',
            '      2  3  6',
        ])

    @pytest.mark.skip
    def test_doctest_report_ndiff(self, testdir):
        result = self._run_doctest_report(testdir, 'ndiff')
        result.stdout.fnmatch_lines([
            '         a  b',
            '      0  1  4',
            '    - 1  2  4',
            '    ?       ^',
            '    + 1  2  5',
            '    ?       ^',
            '      2  3  6',
        ])

    @pytest.mark.parametrize('format', ['none', 'only_first_failure'])
    @pytest.mark.skip
    def test_doctest_report_none_or_only_first_failure(self, testdir, format):
        result = self._run_doctest_report(testdir, format)
        result.stdout.fnmatch_lines([
            'Expected:',
            '       a  b',
            '    0  1  4',
            '    1  2  4',
            '    2  3  6',
            'Got:',
            '       a  b',
            '    0  1  4',
            '    1  2  5',
            '    2  3  6',
        ])

    @pytest.mark.skip
    @pytest.mark.skip
    def test_doctest_report_invalid(self, testdir):
        result = self._run_doctest_report(testdir, 'obviously_invalid_format')
        result.stderr.fnmatch_lines([
            "*error: argument --xdoctest-report: invalid choice: 'obviously_invalid_format' (choose from*"
        ])


class Disabled(object):

    def test_docstring_context_around_error(self, testdir):
        """Test that we show some context before the actual line of a failing
        xdoctest.

        # XDOCTEST DOES NOT SHOW NON-SOURCE CONTEXT

        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_docstring_context_around_error
        """
        testdir.makepyfile('''
            def foo():
                """
                text-line-1
                text-line-2
                text-line-3
                text-line-4
                text-line-5
                text-line-6
                text-line-7
                text-line-8
                text-line-9
                text-line-10
                text-line-11
                >>> 1 + 1
                3

                text-line-after
                """
        ''')
        result = testdir.runpytest('--xdoctest-modules', *EXTRA_ARGS)
        result.stdout.fnmatch_lines([
            '*docstring_context_around_error*',
            '005*text-line-3',
            '006*text-line-4',
            '013*text-line-11',
            '014*>>> 1 + 1',
            'Expected:',
            '    3',
            'Got:',
            '    2',
        ])
        # lines below should be trimmed out
        assert 'text-line-2' not in result.stdout.str()
        assert 'text-line-after' not in result.stdout.str()

    def test_doctest_linedata_missing(self, testdir):
        """
        REPLACES: test_doctest_linedata_missing
        REASON: Static parsing means we do know this line number.

        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_doctest_linedata_missing
        """
        testdir.tmpdir.join('hello.py').write(_pytest._code.Source("""
            class Fun(object):
                @property
                def test(self):
                    '''
                    >>> a = 1
                    >>> 1/0
                    '''
            """))
        result = testdir.runpytest("--xdoctest-modules", *EXTRA_ARGS)
        result.stdout.fnmatch_lines([
            "*hello*",
            "*EXAMPLE LOCATION UNKNOWN, not showing all tests of that example*",
            "*1/0*",
            "*FAILED*ZeroDivision*",
            "*1 failed*",
        ])

    def test_doctestmodule_with_fixtures(self, testdir):
        p = testdir.makepyfile("""
            '''
                >>> dir = getfixture('tmpdir')
                >>> type(dir).__name__
                'LocalPath'
            '''
        """)
        reprec = testdir.inline_run(p, "--xdoctest-modules")
        reprec.assertoutcome(passed=1)

    def test_doctestmodule_three_tests(self, testdir):
        p = testdir.makepyfile("""
            '''
            >>> dir = getfixture('tmpdir')
            >>> type(dir).__name__
            'LocalPath'
            '''
            def my_func():
                '''
                >>> magic = 42
                >>> magic - 42
                0
                '''
            def unuseful():
                pass
            def another():
                '''
                >>> import os
                >>> os is os
                True
                '''
        """)
        reprec = testdir.inline_run(p, "--xdoctest-modules")
        reprec.assertoutcome(passed=3)

    def test_doctestmodule_two_tests_one_fail(self, testdir):
        """
        CommandLine:
            pytest testing/test_plugin.py::TestXDoctest::test_doctestmodule_two_tests_one_fail
        """
        p = testdir.makepyfile("""
            class MyClass(object):
                def bad_meth(self):
                    '''
                    >>> magic = 42
                    >>> magic
                    0
                    '''
                def nice_meth(self):
                    '''
                    >>> magic = 42
                    >>> magic - 42
                    0
                    '''
        """)
        reprec = testdir.inline_run(p, "--xdoctest-modules")
        reprec.assertoutcome(failed=1, passed=1)

    def test_non_ignored_whitespace(self, testdir):
        testdir.makeini("""
            [pytest]
            doctest_optionflags = ELLIPSIS
        """)
        p = testdir.makepyfile("""
            class MyClass(object):
                '''
                >>> a = "foo    "
                >>> print(a)
                foo
                '''
                pass
        """)
        reprec = testdir.inline_run(p, "--xdoctest-modules")
        reprec.assertoutcome(failed=1, passed=0)

    def test_non_ignored_whitespace_glob(self, testdir):
        testdir.makeini("""
            [pytest]
            doctest_optionflags = ELLIPSIS
        """)
        p = testdir.maketxtfile(xdoc="""
            >>> a = "foo    "
            >>> print(a)
            foo
        """)
        reprec = testdir.inline_run(p, "--xdoctest-glob=x*.txt")
        reprec.assertoutcome(failed=1, passed=0)

    def test_ignore_import_errors_on_doctest(self, testdir):
        p = testdir.makepyfile("""
            import asdf

            def add_one(x):
                '''
                >>> add_one(1)
                2
                '''
                return x + 1
        """)

        reprec = testdir.inline_run(p, "--xdoctest-modules",
                                    "--xdoctest-ignore-import-errors")
        reprec.assertoutcome(skipped=1, failed=1, passed=0)

    def test_unicode_doctest(self, testdir):
        """
        Test case for issue 2434: DecodeError on Python 2 when xdoctest contains non-ascii
        characters.
        """
        p = testdir.maketxtfile(test_unicode_doctest="""
            .. xdoctest::

                >>> print(
                ...    "Hi\\n\\nByé")
                Hi
                ...
                Byé
                >>> 1/0  # Byé
                1
        """)
        result = testdir.runpytest(p, *EXTRA_ARGS)
        result.stdout.fnmatch_lines([
            '*FAILED DOCTEST: ZeroDivisionError*',
            '*1 failed*',
        ])

    def test_reportinfo(self, testdir):
        '''
        Test case to make sure that XDoctestItem.reportinfo() returns lineno.
        '''
        p = testdir.makepyfile(test_reportinfo="""
            def foo(x):
                '''
                    >>> foo('a')
                    'b'
                '''
                return 'c'
        """)
        items, reprec = testdir.inline_genitems(p, '--xdoctest-modules')
        reportinfo = items[0].reportinfo()
        assert reportinfo[1] == 1

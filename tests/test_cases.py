from xdoctest.utils.util_misc import _run_case
from xdoctest import utils


def test_properties():
    """
    Test that all doctests are extracted from properties correctly.
    https://github.com/Erotemic/xdoctest/issues/73

    Credit: @trappitsch
    """
    text = _run_case(utils.codeblock(
        '''
        class Test(object):
            @property
            def test(self):
                """
                Example:
                    >>> ini = Test()
                    >>> ini.test
                    3.14
                """
                return 3.14

            @test.setter
            def test(self, s):
                pass
        '''))
    assert 'running 1 test' in text

    text = _run_case(utils.codeblock(
        '''
        class Test(object):
            @property
            def test(self):
                """
                Example:
                    >>> ini = Test()
                    >>> ini.test
                    3.14
                """
                return 3.14
        '''))
    assert 'running 1 test' in text

    text = _run_case(utils.codeblock(
        '''
        class Test(object):
            @property
            def test(self):
                """
                Example:
                    >>> ini = Test()
                    >>> ini.test
                    3.14
                """
                return 3.14

            @test.setter
            def test(self, s):
                """
                Example:
                    >>> ini = Test()
                    >>> ini.test = 3
                """
                pass
        '''))
    assert 'running 1 test' in text

    text = _run_case(utils.codeblock(
        '''
        class Test(object):
            @property
            def test(self):
                return 3.14

            @test.setter
            def test(self, s):
                """
                Example:
                    >>> ini = Test()
                    >>> ini.test = 3
                """
                pass
        '''))
    assert 'running 0 test' in text

    text = _run_case(utils.codeblock(
        '''
        class Test(object):
            @property
            def test(self):
                return 3.14

            @test.setter
            def test(self, s):
                """
                Example:
                    >>> ini = Test()
                    >>> ini.test = 3
                """
                pass

            @test.deleter
            def test(self, s):
                """
                Example:
                    >>> ini = Test()
                    >>> ini.test = 3
                """
                pass
        '''))
    assert 'running 0 test' in text


def test_correct_skipping_on_decorators1():
    """
    This is a weird case similar to the torch dispatch doctest

    ~/code/pytorch/torch/fx/experimental/unification/multipledispatch/core.py

    Something about it causes the skip directive not to be applied to the
    entire thing. Not quite sure what's going on yet.

    The issue was that decorator line numbers were returning as the line of the
    function itself. This mean that the PS1 grouping put the directive in a
    group with logic, which made the parser think it was inline, which meant
    the skip state was cleared after it was executed, so it executed the bad
    code. This fixes that.
    """
    import xdoctest
    from xdoctest import runner
    from os.path import join

    source = utils.codeblock(
        '''
        def dispatch(*types, **kwargs):
            """ blah blah blah blah blah blah blah blah blah blah blah blah
            blah blah blah blah blah blah blah blah

            Example:
                >>> # xdoctest: +SKIP
                >>> @dispatch(int)
                ... def f(x):
                ...     return x + 1
                >>> @dispatch(float)
                ... def f(x):
                ...     return x + 1
                >>> f(3)
                4
                >>> f(3.0)
                4.0
            """
            return lambda x: x
        ''')

    config = {
        # 'global_exec': 'a=1',
        'style': 'google',
    }

    # xdoctest.global_state.DEBUG = 1
    # xdoctest.global_state.DEBUG_PARSER = 10
    # xdoctest.global_state.DEBUG_CORE = 1
    # xdoctest.global_state.DEBUG_RUNNER = 1
    # xdoctest.global_state.DEBUG_DOCTEST = 1

    temp = utils.TempDir()
    dpath = temp.ensure()
    with temp as temp:
        modpath = join(dpath, 'test_example_run.py')

        with open(modpath, 'w') as file:
            file.write(source)

        examples = list(xdoctest.core.parse_doctestables(modpath, style='google', analysis='static'))
        print(f'examples={examples}')

        with utils.CaptureStdout() as cap:
            runner.doctest_module(modpath, 'all', argv=[''], config=config)
        print(cap.text)
        assert '1 skipped' in cap.text


def test_correct_skipping_on_decorators_simple():
    """
    minimal test for decorator skips
    """

    import xdoctest
    from xdoctest import runner
    from os.path import join

    source = utils.codeblock(
        '''
        def _my_decorator():
            """
            Example:
                >>> # xdoctest: +SKIP
                >>> @_my_decorator()
                ... def my_func(x):
                ...     ...
                >>> f(3)
            """
            return
        ''')

    config = {
        'style': 'google',
    }
    temp = utils.TempDir()
    dpath = temp.ensure()
    with temp as temp:
        modpath = join(dpath, 'test_example_run.py')

        with open(modpath, 'w') as file:
            file.write(source)

        examples = list(xdoctest.core.parse_doctestables(modpath, style='google', analysis='static'))
        print(f'examples={examples}')

        with utils.CaptureStdout() as cap:
            runner.doctest_module(modpath, 'all', argv=[''], config=config)
        print(cap.text)
        assert '1 skipped' in cap.text

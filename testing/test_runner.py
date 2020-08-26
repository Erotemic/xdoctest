# -*- coding: utf-8 -*-
from os.path import join
from xdoctest import utils


def test_zero_args():
    """
    python testing/test_runner.py test_zero_args
    """
    from xdoctest import runner

    source = utils.codeblock(
        '''
        # --- HELPERS ---
        def zero_args1(a=1):
            pass


        def zero_args2(*args):
            pass


        def zero_args3(**kwargs):
            pass


        def zero_args4(a=1, b=2, *args, **kwargs):
            pass


        def non_zero_args1(a):
            pass


        def non_zero_args2(a, b):
            pass


        def non_zero_args3(a, b, *args):
            pass


        def non_zero_args4(a, b, **kwargs):
            pass


        def non_zero_args5(a, b=1, **kwargs):
            pass
        ''')

    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_zero_args.py')

        with open(modpath, 'w') as file:
            file.write(source)

        zero_func_names = {
            example.callname
            for example in runner._gather_zero_arg_examples(modpath)
        }
        assert zero_func_names == set(['zero_args1', 'zero_args2',
                                       'zero_args3', 'zero_args4'])


def test_list():
    from xdoctest import runner

    source = utils.codeblock(
        '''
        # --- HELPERS ---
        def real_test1(a=1):
            """
                Example:
                    >>> pass
            """
            pass

        def fake_test1(a=1):
            pass

        def real_test2():
            """
                Example:
                    >>> pass
            """
            pass

        def fake_test2():
            pass
        ''')

    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_list.py')

        with open(modpath, 'w') as file:
            file.write(source)

        with utils.CaptureStdout() as cap:
            runner.doctest_module(modpath, 'list', argv=[''])

        assert 'real_test1' in cap.text
        assert 'real_test2' in cap.text
        assert 'fake_test1' not in cap.text
        assert 'fake_test2' not in cap.text

        # test command=None
        with utils.CaptureStdout() as cap:
            runner.doctest_module(modpath, None, argv=[''])

        assert 'real_test1' in cap.text
        assert 'real_test2' in cap.text
        assert 'fake_test1' not in cap.text
        assert 'fake_test2' not in cap.text


def test_example_run():
    from xdoctest import runner

    source = utils.codeblock(
        '''
        def foo():
            """
                Example:
                    >>> print('i wanna see this')
            """
        ''')

    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_example_run.py')

        with open(modpath, 'w') as file:
            file.write(source)

        with utils.CaptureStdout() as cap:
            runner.doctest_module(modpath, 'foo', argv=[''])

    assert 'i wanna see this' in cap.text


def test_all_disabled():
    """
    pytest testing/test_runner.py::test_all_disabled -s -vv
    python testing/test_runner.py test_all_disabled
    """
    from xdoctest import runner

    source = utils.codeblock(
        '''
        def foo():
            """
                Example:
                    >>> # DISABLE_DOCTEST
                    >>> print('all will' + ' not print this')
            """

        def bar():
            """
                Example:
                    >>> print('all will' + ' print this')
            """
        ''')

    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_all_disabled.py')

        with open(modpath, 'w') as file:
            file.write(source)

        # disabled tests dont run in "all" mode
        with utils.CaptureStdout() as cap:
            runner.doctest_module(modpath, 'all', argv=[''])
        assert 'all will print this' in cap.text
        # print('    ' + cap.text.replace('\n', '\n    '))
        assert 'all will not print this' not in cap.text

        # Running an disabled example explicitly should work
        with utils.CaptureStdout() as cap:
            runner.doctest_module(modpath, 'foo', argv=[''])
        # print('    ' + cap.text.replace('\n', '\n    '))
        assert 'all will not print this' in cap.text


def test_runner_failures():
    """
    python testing/test_runner.py  test_runner_failures
    pytest testing/test_runner.py::test_runner_failures -s
    pytest testing/test_runner.py::test_all_disabled -s
    """
    from xdoctest import runner

    source = utils.codeblock(
        '''
        def test1():
            """
                Example:
                    >>> pass
            """

        def test2():
            """
                Example:
                    >>> assert False, 'test 2.1'

                Example:
                    >>> assert False, 'test 2.2'
            """

        def test3():
            """
                Example:
                    >>> pass

                Example:
                    >>> pass
            """

        def test4():
            """
                Example:
                    >>> assert False, 'test 3'
            """
        ''')

    temp = utils.TempDir()
    temp.ensure()
    # with utils.TempDir() as temp:
    dpath = temp.dpath
    modpath = join(dpath, 'test_runner_failures.py')

    with open(modpath, 'w') as file:
        file.write(source)

    # disabled tests dont run in "all" mode
    with utils.CaptureStdout(supress=True) as cap:
        try:
            runner.doctest_module(modpath, 'all', argv=[''], verbose=1)
        except Exception:
            pass

    print('\nNOTE: the following output is part of a test')
    print(utils.indent(cap.text, '... '))
    print('NOTE: above output is part of a test')

    # assert '.FFF' in cap.text
    assert '3 / 6 passed' in cap.text
    assert '3 failed' in cap.text
    assert '3 passed' in cap.text


def test_run_zero_arg():
    """
    pytest testing/test_runner.py::test_run_zero_arg -s
    """
    from xdoctest import runner

    source = utils.codeblock(
        '''
        def zero_arg_print():
            print('running zero arg')
        ''')

    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_run_zero_arg.py')

        with open(modpath, 'w') as file:
            file.write(source)

        # disabled tests dont run in "all" mode
        with utils.CaptureStdout() as cap:
            try:
                runner.doctest_module(modpath, 'all', argv=[''], verbose=3)
            except Exception:
                pass
        assert 'running zero arg' not in cap.text

        with utils.CaptureStdout() as cap:
            try:
                runner.doctest_module(modpath, 'zero_arg_print', argv=[''], verbose=3)
            except Exception:
                pass
        # print(cap.text)
        assert 'running zero arg' in cap.text


def test_parse_cmdline():
    """
    pytest testing/test_runner.py::test_parse_cmdline -s
    """
    from xdoctest import runner
    # sys.argv could be anything, so just run this for coverage to make sure it doesnt crash
    runner._parse_commandline(command=None, style=None, verbose=None, argv=None)
    # check specifying argv changes style
    assert 'freeform' == runner._parse_commandline(command=None, style=None, verbose=None, argv=['--freeform'])[1]
    assert 'google' == runner._parse_commandline(command=None, style=None, verbose=None, argv=['--google'])[1]
    assert None is runner._parse_commandline(command=None, style=None, verbose=None, argv=['--google'])[0]


def test_runner_config():
    """
    pytest testing/test_runner.py::test_runner_config -s
    """
    from xdoctest import runner

    source = utils.codeblock(
        '''
        def foo():
            """
                Example:
                    >>> print('i wanna see this')
            """
        ''')

    config = {
        'default_runtime_state': {'SKIP': True},
    }

    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_example_run.py')

        with open(modpath, 'w') as file:
            file.write(source)

        with utils.CaptureStdout() as cap:
            runner.doctest_module(modpath, 'foo', argv=[''], config=config)

    assert 'SKIPPED' in cap.text


def test_global_exec():
    """
    pytest testing/test_runner.py::test_global_exec -s
    """
    from xdoctest import runner

    source = utils.codeblock(
        '''
        def foo():
            """
                Example:
                    >>> print(a)
            """
        ''')

    config = {
        'global_exec': 'a=1',
    }

    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_example_run.py')

        with open(modpath, 'w') as file:
            file.write(source)

        with utils.CaptureStdout() as cap:
            runner.doctest_module(modpath, 'foo', argv=[''], config=config)

    assert '1 passed' in cap.text


def test_hack_the_sys_argv():
    """
    Tests hacky solution to issue #76

    pytest testing/test_runner.py::test_global_exec -s

    References:
        https://github.com/Erotemic/xdoctest/issues/76
    """
    from xdoctest import runner

    source = utils.codeblock(
        '''
        def foo():
            """
                Example:
                    >>> # xdoctest: +REQUIRES(--hackedflag)
                    >>> print('This will run if global_exec specified')
            """
        ''')

    import sys
    NEEDS_FIX = '--hackedflag' not in sys.argv

    config = {
        'global_exec': 'import sys; sys.argv.append("--hackedflag")'
    }

    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_example_run.py')

        with open(modpath, 'w') as file:
            file.write(source)

        with utils.CaptureStdout() as cap:
            runner.doctest_module(modpath, 'foo', argv=[''], config=config)

    if NEEDS_FIX:
        # Fix the global state
        sys.argv.remove('--hackedflag')

    # print(cap.text)
    assert '1 passed' in cap.text


if __name__ == '__main__':
    """
    CommandLine:
        pytest testing/test_runner.py -s
        pytest testing/test_runner.py -s
        python testing/test_runner.py test_zero_args
    """
    # import pytest
    # pytest.main([__file__])
    import xdoctest
    xdoctest.doctest_module(__file__)

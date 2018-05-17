# -*- coding: utf-8 -*-
"""
Need to enhance the tracebacks to spit out something more useful

TODO: rename to test traceback
"""
from os.path import join
from xdoctest import utils
from xdoctest import runner


def _run_case(source):
    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_list.py')

        with open(modpath, 'w') as file:
            file.write(source)

        with utils.CaptureStdout(supress=False) as cap:
            runner.doctest_module(modpath, 'all', argv=[''])
        return cap.text


def test_fail_call_onefunc():
    text = _run_case(utils.codeblock(
        '''
        def func(a):
            """
            Example:
                >>> a = 1
                >>> func(a)
            """
            a = []()
            return a
        '''))
    assert '---> func(a)' in text


def test_fail_call_twofunc():
    text = _run_case(utils.codeblock(
        '''
        def func(a):
            """
            Example:
                >>> a = 1
                >>> func(a)
            """
            a = []()
            return a

        def func2(a):
            """
            Example:
                >>> pass
            """
            pass
        '''))
    assert text
    assert '---> func(a)' in text


def test_fail_inside_twofunc():
    text = _run_case(utils.codeblock(
        '''
        def func(a):
            """
            Example:
                >>> print('not failed')
                >>> # just a comment
                >>> print(("foo"
                ...        "bar"))
                >>> a = []()
                >>> func(a)
            """
            return a

        def func2(a):
            """
            Example:
                >>> pass
            """
            pass
        '''))
    assert text
    assert '---> a = []()' in text


def test_fail_inside_onefunc():
    """
        python ~/code/xdoctest/testing/test_cases.py test_fail_inside_onefunc

    """
    text = _run_case(utils.codeblock(
        '''
        def func(a):
            """
            Example:
                >>> x = 1
                >>> # just a comment
                >>> print(("foo"
                ...        "bar"))
                foobar
                >>> a = []()
                >>> func(a)
            """
            return a
        '''))
    assert text
    assert '---> a = []()' in text


if __name__ == '__main__':
    """
    CommandLine:
        export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/xdoctest/testing
        python ~/code/xdoctest/testing/test_cases.py
        pytest ~/code/xdoctest/testing/test_cases.py -s
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

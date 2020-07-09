# -*- coding: utf-8 -*-
"""
Need to enhance the tracebacks to spit out something more useful
"""
from xdoctest import utils
from xdoctest.utils.util_misc import _run_case


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
    assert '>>> func(a)' in text
    assert 'rel: 2, abs: 5' in text


def test_fail_call_twofunc():
    """
        python ~/code/xdoctest/testing/test_traceback.py test_fail_call_twofunc

    """
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
    assert '>>> func(a)' in text
    assert 'rel: 2, abs: 5,' in text


def test_fail_inside_twofunc():
    """
        python ~/code/xdoctest/testing/test_traceback.py test_fail_inside_twofunc

    """
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
    assert '>>> a = []()' in text
    assert 'rel: 5, abs: 8' in text


def test_fail_inside_onefunc():
    """
        python ~/code/xdoctest/testing/test_traceback.py test_fail_inside_onefunc

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
    assert '>>> a = []()' in text
    assert 'rel: 6, abs: 9,' in text

def test_failure_linenos():
    """
    Example:
        python ~/code/xdoctest/testing/test_linenos.py test_failure_linenos

    Example:
        >>> test_failure_linenos()
    """
    text = _run_case(utils.codeblock(
        r'''
        def bar(a):
            return a

        class Foo:
            @bar
            @staticmethod
            def func(a):
                """
                Example:
                    >>> # Perform some passing tests before we call failing code
                    >>> Foo.func(0)
                    0
                    >>> # call the failing code
                    >>> if True:
                    >>>     assert 1 == 2
                    >>> # Do stuff that wont be executed
                    >>> Foo.func(0)
                    0
                    >>> Foo.func(1)
                    1
                """
                return a
        '''))

    assert 'line 15' in text
    assert 'line 6' in text
    assert text


# There are three different types of traceback failure
# (1) failure of code within the doctest
# (2) failure of code called by the doctest
# (3) failure of doctest got/want syntax

# TODO: Add checks on the line numbers reported in the tracebacks for these
# function.
# TODO: Check that the formatting of the tracebacks for each case are user
# friendly

"""

SeeAlso:
    # This plugin tests also checks line numbers. Make sure we dont break it
    pytest testing/test_plugin.py::TestXDoctest::test_doctest_property_lineno -v -s

"""


def test_lineno_failcase_gotwant():
    """
        python ~/code/xdoctest/testing/test_linenos.py test_lineno_failcase_gotwant

    """
    text = _run_case(utils.codeblock(
        '''
        def func(a):
            """
            Example:
                >>> got = func('foo')
                >>> print(got)
                bar
            """
            return a
        '''))
    assert text
    assert 'line 3' in text
    assert 'line 6' in text


def test_lineno_failcase_called_code():
    """
        python ~/code/xdoctest/testing/test_linenos.py test_lineno_failcase_called_code
        python ~/code/xdoctest/testing/test_linenos.py

    """
    text = _run_case(utils.codeblock(
        r'''
        def func(a):
            """
            Example:
                >>> func(0)
                >>> # this doesnt do anything
                >>> print('this passes')
                this passes
                >>> # call the failing code
                >>> func(3)
            """
            if a > 0:
                nested_failure(a)
            return a

        def nested_failure(a):
            if a > 0:
                nested_failure(a - 1)
            else:
                raise Exception('fail case')
        '''))
    assert 'rel: 6, abs: 9,' in text
    assert text


def test_lineno_failcase_doctest_code():
    """
        python ~/code/xdoctest/testing/test_linenos.py test_lineno_failcase_doctest_code

    """
    text = _run_case(utils.codeblock(
        r'''
        def bar():
            pass

        def func(a):
            """
            Example:
                >>> # Perform some passing tests before we call failing code
                >>> func(0)
                0
                >>> # call the failing code
                >>> assert 1 == 2
                >>> # Do stuff that wont be executed
                >>> func(0)
                0
                >>> func(1)
                1
            """
            return a
        '''))
    assert 'rel: 5, abs: 11,' in text
    assert text



if __name__ == '__main__':
    """
    CommandLine:
        export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/xdoctest/testing
        python ~/code/xdoctest/testing/test_traceback.py
        pytest ~/code/xdoctest/testing/test_traceback.py -s
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

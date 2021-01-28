# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from xdoctest import doctest_example
from xdoctest import utils
from xdoctest import constants
from xdoctest import checker


def test_exit_test_exception():
    """
    pytest testing/test_doctest_example.py::test_exit_test_exception
    """
    string = utils.codeblock(
        '''
        >>> from xdoctest import ExitTestException
        >>> raise ExitTestException()
        >>> 0 / 0  # should never reach this
        2
        ''')
    self = doctest_example.DocTest(docsrc=string)
    result = self.run(on_error='raise')
    assert result['passed']


def test_failed_assign_want():
    """
    pytest testing/test_doctest_example.py::test_exit_test_exception
    """
    string = utils.codeblock(
        '''
        >>> name = 'foo'
        'anything'
        ''')
    self = doctest_example.DocTest(docsrc=string)
    result = self.run(on_error='return', verbose=0)
    assert result['failed']
    fail_text = '\n'.join(self.repr_failure())
    assert 'Got nothing' in fail_text


def test_continue_ambiguity():
    """
    pytest testing/test_doctest_example.py::test_exit_test_exception
    """
    string = utils.codeblock(
        '''
        >>> class Lowerer(object):
        ...     def __init__(self):
        ...         self.cache = LRI()
        ...
        ...     def lower(self, text):
        ...         return text.lower()
        ...
        ''')
    self = doctest_example.DocTest(docsrc=string)
    result = self.run(on_error='return', verbose=3)
    assert result['passed']


def test_failed_assign_want():
    """
    pytest testing/test_doctest_example.py::test_exit_test_exception
    xdoctest ~/code/xdoctest/testing/test_doctest_example.py test_failed_assign_want
    """
    string = utils.codeblock(
        '''
        >>> name = 'foo'
        'anything'
        ''')
    self = doctest_example.DocTest(docsrc=string)
    result = self.run(on_error='return', verbose=0)
    assert result['failed']
    fail_text = '\n'.join(self.repr_failure())
    assert 'Got nothing' in fail_text


def test_contination_want_ambiguity():
    """
    xdoctest ~/code/xdoctest/testing/test_doctest_example.py test_contination_want_ambiguity
    """
    string = utils.codeblock(
        '''
        >>> class Lowerer(object):
        ...     def __init__(self):
        ...         self.cache = LRI()
        ...
        ...     def lower(self, text):
        ...         return text.lower()
        ...
        ''')
    self = doctest_example.DocTest(docsrc=string)
    result = self.run(on_error='return', verbose=3)
    assert result['passed']


def test_multiline_list():
    """
    pytest testing/test_doctest_example.py::test_multiline_list
    """
    string = utils.codeblock(
        '''
        >>> x = [1, 2, 3,
        >>>      4, 5, 6]
        >>> print(len(x))
        6
        ''')
    self = doctest_example.DocTest(docsrc=string)
    result = self.run(on_error='raise')
    assert result['passed']


def test_failure():
    string = utils.codeblock(
        '''
        >>> i = 0
        >>> 0 / i
        2
        ''')
    self = doctest_example.DocTest(docsrc=string, lineno=1000)
    self._parse()
    try:
        self.run(on_error='raise')
    except ZeroDivisionError as ex:
        pass
    else:
        raise AssertionError('should have gotten zero division')

    result = self.run(on_error='return')
    assert not result['passed']


def test_format_src():
    """
    python testing/test_doctest_example.py test_format_src

    pytest testing/test_doctest_example.py::test_format_src -s -v
    """
    string = utils.codeblock(
        '''
        >>> i = 0
        >>> 0 / i
        2
        ''')
    string_with_lineno = utils.codeblock(
        '''
        1 >>> i = 0
        2 >>> 0 / i
          2
        ''').replace('!', ' ')
    self = doctest_example.DocTest(docsrc=string)
    self._parse()

    assert self.format_src(colored=0, linenos=1) == string_with_lineno
    assert self.format_src(colored=0, linenos=0) == string
    assert utils.strip_ansi(self.format_src(colored=1, linenos=1)) == string_with_lineno
    assert utils.strip_ansi(self.format_src(colored=1, linenos=0)) == string


def test_eval_expr_capture():
    """
    pytest testing/test_doctest_example.py::test_eval_expr_capture -s
    """
    docsrc = utils.codeblock(
        '''
        >>> x = 3
        >>> y = x + 2
        >>> y + 2
        2
        ''')
    self = doctest_example.DocTest(docsrc=docsrc)
    self._parse()
    p1, p2 = self._parts

    # test_globals = {}
    # code1 = compile(p1.source, '<string>', 'exec')
    # exec(code1, test_globals)
    # code2 = compile(p2.source, '<string>', 'eval')
    # result = eval(code2, test_globals)
    try:
        self.run()
    except Exception as ex:
        assert hasattr(ex, 'output_difference')
        msg = ex.output_difference(colored=False)
        assert msg == utils.codeblock(
            '''
            Expected:
                2
            Got:
                7
            ''')


def test_run_multi_want():
    docsrc = utils.codeblock(
        '''
        >>> x = 2
        >>> x
        2
        >>> 'string'
        'string'
        >>> print('string')
        string
        ''')
    self = doctest_example.DocTest(docsrc=docsrc)
    self.run()

    result = self.run()

    assert result['passed']
    assert list(self.logged_stdout.values()) == ['', '', '', 'string\n']
    assert list(self.logged_evals.values()) == [constants.NOT_EVALED, 2, 'string', None]


def test_comment():
    docsrc = utils.codeblock(
        '''
        >>> # foobar
        ''')
    self = doctest_example.DocTest(docsrc=docsrc)
    self._parse()
    assert len(self._parts) == 1
    self.run(verbose=0)

    docsrc = utils.codeblock(
        '''
        >>> # foobar
        >>> # bazbiz
        ''')
    self = doctest_example.DocTest(docsrc=docsrc)
    self._parse()
    assert len(self._parts) == 1
    self.run(verbose=0)

    docsrc = utils.codeblock(
        '''
        >>> # foobar
        >>> x = 0
        >>> x / 0
        >>> # bazbiz
        ''')
    self = doctest_example.DocTest(docsrc=docsrc, lineno=1)
    self._parse()
    assert len(self._parts) == 1
    result = self.run(on_error='return', verbose=0)
    assert not result['passed']

    assert self.failed_lineno() == 3


def test_want_error_msg():
    """
    python testing/test_doctest_example.py test_want_error_msg
    pytest testing/test_doctest_example.py::test_want_error_msg
    """
    string = utils.codeblock(
        '''
        >>> raise Exception('everything is fine')
        Traceback (most recent call last):
        Exception: everything is fine
        ''')
    self = doctest_example.DocTest(docsrc=string)
    result = self.run(on_error='raise')
    assert result['passed']


def test_want_error_msg_failure():
    """
    python testing/test_doctest_example.py test_want_error_msg_failure
    pytest testing/test_doctest_example.py::test_want_error_msg_failure
    """
    string = utils.codeblock(
        '''
        >>> raise Exception('everything is NOT fine')
        Traceback (most recent call last):
        Exception: everything is fine
        ''')

    self = doctest_example.DocTest(docsrc=string)
    import pytest
    with pytest.raises(checker.GotWantException):
        self.run(on_error='raise')


if __name__ == '__main__':
    """
    CommandLine:
        export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/xdoctest/testing
        python ~/code/xdoctest/testing/test_doctest_example.py
        xdoctest ~/code/xdoctest/testing/test_doctest_example.py zero-args
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

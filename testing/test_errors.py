# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from os.path import join
import warnings
import pytest
from xdoctest import runner
from xdoctest import core
from xdoctest import exceptions
from xdoctest import utils


def test_parse_syntax_error():
    """
    CommandLine:
        python testing/test_errors.py test_parse_syntax_error
    """
    docstr = utils.codeblock(
        '''
        Example:
            >>> x = 0
            >>> 3 = 5
            ''')

    info = {'callname': 'test_synerr', 'lineno': 42}

    # Eager parsing should cause no doctests with errors to be found
    # and warnings should be raised
    with warnings.catch_warnings(record=True) as f_warnlist:
        f_doctests = list(core.parse_docstr_examples(docstr, style='freeform',
                                                     **info))

    with warnings.catch_warnings(record=True) as g_warnlist:
        g_doctests = list(core.parse_docstr_examples(docstr, style='google',
                                                     **info))

    assert len(g_warnlist) == 1
    assert len(f_warnlist) == 1
    assert len(g_doctests) == 0
    assert len(f_doctests) == 0

    # Google style can find doctests with bad syntax, but parsing them
    # results in an error.
    g_doctests2 = list(core.parse_google_docstr_examples(docstr,
                                                         eager_parse=False,
                                                         **info))
    assert len(g_doctests2) == 1
    for example in g_doctests2:
        with pytest.raises(exceptions.DoctestParseError):
            example._parse()


def test_runner_syntax_error():
    """
        python testing/test_errors.py test_runner_syntax_error
    """
    source = utils.codeblock(
        '''
        def test_parsetime_syntax_error1():
            """
                Example:
                    >>> from __future__ import print_function
                    >>> print 'Parse-Time Syntax Error'
            """

        def test_parsetime_syntax_error2():
            """
                Example:
                    >>> def bad_syntax() return for
            """

        def test_runtime_error():
            """
                Example:
                    >>> print('Runtime Error {}'.format(5 / 0))
            """

        def test_runtime_name_error():
            """
                Example:
                    >>> print('Name Error {}'.format(foo))
            """

        def test_runtime_warning():
            """
                Example:
                    >>> import warnings
                    >>> warnings.warn('in-code warning')
            """
        ''')

    temp = utils.TempDir(persist=True)
    temp.ensure()
    dpath = temp.dpath
    modpath = join(dpath, 'test_runner_syntax_error.py')
    open(modpath, 'w').write(source)

    with utils.CaptureStdout() as cap:
        runner.doctest_module(modpath, 'all', argv=[''], style='freeform',
                              verbose=0)

    print(utils.indent(cap.text))

    assert '1 run-time warnings' in cap.text
    assert '2 parse-time warnings' in cap.text

    # Assert summary line
    assert '3 warnings' in cap.text
    assert '2 failed' in cap.text
    assert '1 passed' in cap.text


if __name__ == '__main__':
    r"""
    CommandLine:
        export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/xdoctest/testing
        python ~/code/xdoctest/testing/test_errors.py
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

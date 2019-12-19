# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from os.path import join
import six
import warnings
import pytest
from xdoctest import runner
from xdoctest import core
from xdoctest import exceptions
from xdoctest import utils
from xdoctest.utils.util_misc import _run_case


# def _check_syntaxerror_behavior():
#     import ubelt as ub
#     source_block = ub.codeblock(
#         '''
#         x = 3
#         3 = 5
#         ''')
#     try:
#         compile(source_block, filename='<string>', mode='exec')
#     except SyntaxError as ex1:
#         print('ex1.text = {!r}'.format(ex1.text))
#         print('ex1.offset = {!r}'.format(ex1.offset))
#         print('ex1.lineno = {!r}'.format(ex1.lineno))

#     import ast
#     try:
#         pt = ast.parse(source_block)
#     except SyntaxError as ex2:
#         print('ex2.text = {!r}'.format(ex2.text))
#         print('ex2.offset = {!r}'.format(ex2.offset))
#         print('ex2.lineno = {!r}'.format(ex2.lineno))

#     fpath = join(ub.ensure_app_cache_dir('xdoctest', 'test'), 'source.py')
#     ub.writeto(fpath, source_block)
#     try:
#         compile(source_block, filename=fpath, mode='exec')
#     except SyntaxError as ex2:
#         print('ex2.text = {!r}'.format(ex2.text))
#         print('ex2.offset = {!r}'.format(ex2.offset))
#         print('ex2.lineno = {!r}'.format(ex2.lineno))

#     import tempfile
#     import ast
#     temp = tempfile.NamedTemporaryFile()
#     temp.file.write((source_block + '\n').encode('utf8'))
#     temp.file.seek(0)
#     try:
#         ast.parse(source_block, temp.name)
#     except SyntaxError as ex2:
#         print('ex2.text = {!r}'.format(ex2.text))
#         print('ex2.offset = {!r}'.format(ex2.offset))
#         print('ex2.lineno = {!r}'.format(ex2.lineno))
#         raise


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

    for w in g_warnlist:
        print(w.message)

    for w in f_warnlist:
        print(w.message)

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

        xdoctest -m testing/test_errors.py test_runner_syntax_error
    """
    source = utils.codeblock(
        r'''
        def demo_parsetime_syntax_error1():
            """
                Example:
                    >>> from __future__ import print_function
                    >>> print 'Parse-Time Syntax Error'
            """

        def demo_parsetime_syntax_error2():
            """
                Example:
                    >>> def bad_syntax() return for
            """

        def demo_runtime_error():
            """
                Example:
                    >>> print('Runtime Error {}'.format(5 / 0))
            """

        def demo_runtime_name_error():
            """
                Example:
                    >>> print('Name Error {}'.format(foo))
            """

        def demo_runtime_warning():
            """
                Example:
                    >>> import warnings
                    >>> warnings.warn('in-code warning')
            """
        ''')

    temp = utils.TempDir(persist=True)
    temp.ensure()
    dpath = temp.dpath
    modpath = join(dpath, 'demo_runner_syntax_error.py')
    with open(modpath, 'w') as file:
        file.write(source)

    with utils.CaptureStdout() as cap:
        runner.doctest_module(modpath, 'all', argv=[''], style='freeform',
                              verbose=1)

    print('CAPTURED [[[[[[[[')
    print(utils.indent(cap.text))
    print(']]]]]]]] # CAPTURED')

    if six.PY2:
        captext = utils.ensure_unicode(cap.text)
    else:
        captext = cap.text

    if True or not six.PY2:  # Why does this have issues on the dashboards?
        assert '1 run-time warnings' in captext
        assert '2 parse-time warnings' in captext

        # Assert summary line
        assert '3 warnings' in captext
        assert '2 failed' in captext
        assert '1 passed' in captext


def test_parse_doctset_error():
    source = utils.codeblock(
        '''
        def func_with_an_unparsable_google_docstr(a):
            """
            This function will have an unparsable google docstr

            Args:
                a (int): a number

            Example:
                >>> a = "\\''' + '''n"
                >>> func(a)
            """
            pass

          ''')
    text = _run_case(source, style='google')
    text = _run_case(source, style='freeform')
    del text


def test_extract_got_exception():
    """
    Make a repr that fails

    CommandLine:
        xdoctest -m ~/code/xdoctest/testing/test_errors.py test_extract_got_exception
    """

    source = utils.codeblock(
        '''
        class MyObj(object):
            """
            Example:
                >>> a = MyObj()
                >>> a
                you cant always get what you want
            """
            def __repr__(self):
                raise Exception('this repr fails')
          ''')
    text = _run_case(source, style='google')
    assert 'ExtractGotReprException' in text


if __name__ == '__main__':
    """
    CommandLine:
        export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/xdoctest/testing
        python ~/code/xdoctest/testing/test_errors.py
        pytest ~/code/xdoctest/testing/test_errors.py -s --verbose

    CommandLine:
        xdoctest -m ~/code/xdoctest/testing/test_errors.py test_extract_got_exception zero
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

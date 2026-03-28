import warnings
from os.path import join

import pytest

from xdoctest import core, exceptions, runner, utils
from xdoctest.utils.util_misc import _run_case


def test_parse_syntax_error() -> None:
    """
    CommandLine:
        python tests/test_errors.py test_parse_syntax_error
    """
    docstr = utils.codeblock(
        """
        Example:
            >>> x = 0
            >>> 3 = 5
            """
    )

    info = {
        'callname': 'test_synerr',
        'lineno': 42,
        'fpath': None,
        'parser_kw': None,
    }

    # Eager parsing should cause no doctests with errors to be found
    # and warnings should be raised
    with warnings.catch_warnings(record=True) as f_warnlist:
        f_doctests = list(
            core.parse_docstr_examples(
                docstr,
                callname=info['callname'],
                lineno=info['lineno'],
                style='freeform',
                modpath=None,
                fpath=None,
                parser_kw=None,
            )
        )

    with warnings.catch_warnings(record=True) as g_warnlist:
        g_doctests = list(
            core.parse_docstr_examples(
                docstr,
                callname=info['callname'],
                lineno=info['lineno'],
                style='google',
                modpath=None,
                fpath=None,
                parser_kw=None,
            )
        )

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
    g_doctests2 = list(
        core.parse_google_docstr_examples(
            docstr,
            callname=info['callname'],
            lineno=info['lineno'],
            eager_parse=False,
            modpath=None,
            fpath=None,
        )
    )
    assert len(g_doctests2) == 1
    for example in g_doctests2:
        with pytest.raises(exceptions.DoctestParseError):
            example._parse()


def test_runner_syntax_error() -> None:
    """
    python tests/test_errors.py test_runner_syntax_error
    pytest tests/test_errors.py -k test_runner_syntax_error

    xdoctest -m tests/test_errors.py test_runner_syntax_error
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
        '''
    )

    temp = utils.TempDir(persist=True)
    temp.ensure()
    dpath = temp.dpath
    assert dpath is not None
    modpath = join(dpath, 'demo_runner_syntax_error.py')
    with open(modpath, 'w') as file:
        file.write(source)

    with utils.CaptureStdout() as cap:
        runner.doctest_module(
            modpath, 'all', argv=[''], style='freeform', verbose=1
        )

    print('CAPTURED [[[[[[[[')
    assert cap.text is not None
    print(utils.indent(cap.text))
    print(']]]]]]]] # CAPTURED')

    captext = cap.text

    assert '1 run-time warnings' in captext
    assert '2 parse-time warnings' in captext

    # Assert summary line
    assert '3 warnings' in captext
    assert '2 failed' in captext
    assert '1 passed' in captext


def test_parse_doctset_error() -> None:
    source = utils.codeblock(
        '''
        def func_with_an_unparsable_google_docstr(a):
            """
            This function will have an unparsable google docstr

            Args:
                a (int): a number

            Example:
                >>> a = "\\'''
        + '''n"
                >>> func(a)
            """
            pass

          '''
    )
    text = _run_case(source, style='google')
    text = _run_case(source, style='freeform')
    del text


def test_extract_got_exception() -> None:
    """
    Make a repr that fails

    CommandLine:
        xdoctest -m ~/code/xdoctest/tests/test_errors.py test_extract_got_exception
    """

    source = utils.codeblock(
        '''
        class MyObj:
            """
            Example:
                >>> a = MyObj()
                >>> a
                you cant always get what you want
            """
            def __repr__(self):
                raise Exception('this repr fails')
          '''
    )
    text = _run_case(source, style='google')
    assert text is not None
    assert 'ExtractGotReprException' in text


if __name__ == '__main__':
    """
    CommandLine:
        export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/xdoctest/tests
        python ~/code/xdoctest/tests/test_errors.py
        pytest ~/code/xdoctest/tests/test_errors.py -s --verbose

    CommandLine:
        xdoctest -m ~/code/xdoctest/tests/test_errors.py test_extract_got_exception zero
    """
    import xdoctest

    xdoctest.doctest_module(__file__)

# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from os.path import join
from xdoctest import core
from xdoctest import utils


def test_failure():
    string = utils.codeblock(
        '''
        >>> i = 0
        >>> 0 / i
        2
        ''')
    self = core.DocTest(docsrc=string, lineno=1000)
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
    self = core.DocTest(docsrc=string)
    self._parse()

    assert self.format_src(colored=0, linenos=1) == string_with_lineno
    assert self.format_src(colored=0, linenos=0) == string
    assert utils.strip_ansi(self.format_src(colored=1, linenos=1)) == string_with_lineno
    assert utils.strip_ansi(self.format_src(colored=1, linenos=0)) == string


def test_eval_expr_capture():
    docsrc = utils.codeblock(
        '''
        >>> x = 3
        >>> y = x + 2
        >>> y + 2
        2
        ''')
    self = core.DocTest(docsrc=docsrc)
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
        msg = ex.output_difference()
        print(msg)
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
    self = core.DocTest(docsrc=docsrc)
    self.run()

    result = self.run()

    assert result['passed']
    assert list(self.logged_stdout.values()) == ['', '', '', 'string\n']
    assert list(self.logged_evals.values()) == [core.NOT_EVALED, 2, 'string', None]


def test_comment():
    docsrc = utils.codeblock(
        '''
        >>> # foobar
        ''')
    self = core.DocTest(docsrc=docsrc)
    self._parse()
    assert len(self._parts) == 1
    self.run(verbose=0)

    docsrc = utils.codeblock(
        '''
        >>> # foobar
        >>> # bazbiz
        ''')
    self = core.DocTest(docsrc=docsrc)
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
    self = core.DocTest(docsrc=docsrc, lineno=1)
    self._parse()
    assert len(self._parts) == 1
    result = self.run(on_error='return', verbose=0)
    assert not result['passed']

    assert self.failed_lineno() == 3


def test_mod_lineno():
    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_mod_lineno.py')
        source = utils.codeblock(
            '''
            class Fun(object):  #1
                @property
                def test(self):
                    """         # 4
                    >>> a = 1
                    >>> 1 / 0
                    """
            ''')
        with open(modpath, 'w') as file:
            file.write(source)
        from xdoctest import core
        doctests = list(core.parse_doctestables(modpath, style='freeform'))
        assert len(doctests) == 1
        self = doctests[0]

        # print(self._parts[0])
        assert self.lineno == 5
        # print(self.format_src())
        self.config['colored'] = False
        assert self.format_src(offset_linenos=False).strip().startswith('1')
        assert self.format_src(offset_linenos=True).strip().startswith('5')

        with utils.PythonPathContext(dpath):
            status = self.run(verbose=10, on_error='return')

        assert not status['passed']


def test_mod_globals():
    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_mod_globals.py')
        source = utils.codeblock(
            '''
            X = 10
            def test(self):
                """
                >>> X
                10
                """
            ''')
        with open(modpath, 'w') as file:
            file.write(source)
        from xdoctest import core
        doctests = list(core.parse_doctestables(modpath, style='freeform'))
        assert len(doctests) == 1
        self = doctests[0]

        with utils.PythonPathContext(dpath):
            status = self.run(verbose=0, on_error='return')
        assert status['passed']
        assert self.logged_evals[0] == 10


def test_show_entire():
    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_show_entire.py')
        source = utils.codeblock(
            '''
            def foo():
                """
                Prefix

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
            ''')
        with open(modpath, 'w') as file:
            file.write(source)
        from xdoctest import core

        # calldefs = core.module_calldefs(modpath)
        # docline = calldefs['foo'].doclineno
        # docstr = calldefs['foo'].docstr
        # all_parts = parser.DoctestParser().parse(docstr)
        # assert docline == 2

        doctests = list(core.parse_doctestables(modpath, style='freeform'))
        assert len(doctests) == 1
        self = doctests[0]
        self.config['colored'] = False
        print(self.lineno)
        print(self._parts[0].line_offset)
        print(self.format_src())
        assert self.format_src(offset_linenos=True).strip().startswith('6')
        assert self.format_src(offset_linenos=False).strip().startswith('1')

        with utils.PythonPathContext(dpath):
            status = self.run(verbose=0, on_error='return')
        assert not status['passed']


def test_freeform_parse_lineno():
    docstr = utils.codeblock(
        '''
        >>> print('line1')  # test.line=1, offset=0

        Example:
            >>> x = 0  # test.line=4, offset=0

        DisableExample:
            >>> x = 0  # test.line=7, offset=0

        Example:
            >>> True  # test.line=10, offset=0
            True

        Example:
            >>> False  # test.line=14, offset=0
            >>> False  # test.line=15, offset=1
            False
            >>> True  # test.line=17, offset=3

        junk text
        >>> x = 4       # line 20, offset 0
        >>> x = 5 + x   # line 21, offset 1
        33
        >>> x = 6 + x   # line 23, offset 3

        text-line-after
        ''')

    from xdoctest import core
    doctests = list(core.parse_freeform_docstr_examples(docstr, lineno=1))
    assert  [test.lineno for test in doctests] == [1, 4, 10, 14, 20]

    for test in doctests:
        assert test._parts[0].line_offset == 0
        offset = 0
        for p in test._parts:
            assert p.line_offset == offset
            offset += p.n_lines

    doctests = list(core.parse_google_docstr_examples(docstr, lineno=1))
    assert  [test.lineno for test in doctests] == [4, 10, 14]

    for test in doctests:
        test._parse()
        assert test._parts[0].line_offset == 0
        offset = 0
        for p in test._parts:
            assert p.line_offset == offset
            offset += p.n_lines


def test_exit_test_exception():
    """
    pytest testing/test_core.py::test_exit_test_exception
    """
    string = utils.codeblock(
        '''
        >>> from xdoctest.core import ExitTestException
        >>> raise ExitTestException()
        >>> 0 / 0  # should never reach this
        2
        ''')
    self = core.DocTest(docsrc=string)
    result = self.run(on_error='raise')
    assert result['passed']


def test_multiline_list():
    """
    pytest testing/test_core.py::test_multiline_list
    """
    string = utils.codeblock(
        '''
        >>> x = [1, 2, 3,
        >>>      4, 5, 6]
        >>> print(len(x))
        6
        ''')
    self = core.DocTest(docsrc=string)
    result = self.run(on_error='raise')
    assert result['passed']


def test_collect_module_level():
    """
    pytest testing/test_core.py::test_collect_module_level

    Ignore:
        temp = utils.TempDir()
    """
    temp = utils.TempDir()
    dpath = temp.ensure()
    modpath = join(dpath, 'test_collect_module_level.py')
    source = utils.codeblock(
        '''
        """
        >>> pass
        """
        ''')
    with open(modpath, 'w') as file:
        file.write(source)
    from xdoctest import core
    doctests = list(core.parse_doctestables(modpath, style='freeform'))
    assert len(doctests) == 1
    self = doctests[0]
    assert self.callname == '__doc__'
    self.config['colored'] = False
    assert self.format_src(offset_linenos=True).strip().startswith('2')
    assert self.format_src(offset_linenos=False).strip().startswith('1')

    with utils.PythonPathContext(dpath):
        status = self.run(verbose=0, on_error='return')
    assert status['passed']
    temp.cleanup()


def test_collect_module_level_singleline():
    """
    pytest testing/test_core.py::test_collect_module_level

    Ignore:
        temp = utils.TempDir()
    """
    temp = utils.TempDir()
    dpath = temp.ensure()
    modpath = join(dpath, 'test_collect_module_level_singleline.py')
    source = utils.codeblock(
        '''">>> pass"''')
    with open(modpath, 'w') as file:
        file.write(source)
    from xdoctest import core
    doctests = list(core.parse_doctestables(modpath, style='freeform'))
    assert len(doctests) == 1
    self = doctests[0]
    assert self.callname == '__doc__'
    self.config['colored'] = False
    assert self.format_src(offset_linenos=True).strip().startswith('1')
    assert self.format_src(offset_linenos=False).strip().startswith('1')

    with utils.PythonPathContext(dpath):
        status = self.run(verbose=0, on_error='return')
    assert status['passed']
    temp.cleanup()


if __name__ == '__main__':
    r"""
    CommandLine:
        export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/xdoctest/testing
        python ~/code/xdoctest/testing/test_core.py
        pytest testing/test_core.py -vv
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

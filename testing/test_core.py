import sys


class PythonPathContext(object):
    def __init__(self, dpath):
        self.dpath = dpath

    def __enter__(self):
        sys.path.append(self.dpath)

    def __exit__(self, a, b, c):
        assert sys.path[-1] == self.dpath
        sys.path.pop()


def test_failure():
    import ubelt as ub
    from xdoctest import core
    string = ub.codeblock(
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
    import ubelt as ub
    from xdoctest import core
    string = ub.codeblock(
        '''
        >>> i = 0
        >>> 0 / i
        2
        ''')
    string_with_lineno = ub.codeblock(
        '''
        1 >>> i = 0
        2 >>> 0 / i
          2
        ''').replace('!', ' ')
    self = core.DocTest(docsrc=string)
    self._parse()

    def strip_ansi(text):
        """
        Removes all ansi directives from the string
        Helper to remove ansi from length calculation
        References: http://stackoverflow.com/questions/14693701remove-ansi
        """
        import re
        ansi_escape = re.compile(r'\x1b[^m]*m')
        return ansi_escape.sub('', text)
    assert self.format_src(colored=0, linenums=1) == string_with_lineno
    assert self.format_src(colored=0, linenums=0) == string
    assert strip_ansi(self.format_src(colored=1, linenums=1)) == string_with_lineno
    assert strip_ansi(self.format_src(colored=1, linenums=0)) == string


def test_eval_expr_capture():
    import ubelt as ub
    from xdoctest import core

    docsrc = ub.codeblock(
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
        assert msg == ub.codeblock(
            '''
            Expected:
                2
            Got:
                7
            ''')


def test_run_multi_want():
    """
    """
    import ubelt as ub
    from xdoctest import core
    docsrc = ub.codeblock(
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
    self.stdout_results
    self.evaled_results

    assert result['passed']
    assert self.stdout_results == ['', '', '', 'string\n']
    assert self.evaled_results == [None, '2', "'string'", 'None']


def test_comment():
    import ubelt as ub
    from xdoctest import core
    docsrc = ub.codeblock(
        '''
        >>> # foobar
        ''')
    self = core.DocTest(docsrc=docsrc)
    self._parse()
    assert len(self._parts) == 1
    self.run()

    docsrc = ub.codeblock(
        '''
        >>> # foobar
        >>> # bazbiz
        ''')
    self = core.DocTest(docsrc=docsrc)
    self._parse()
    assert len(self._parts) == 1
    self.run()

    docsrc = ub.codeblock(
        '''
        >>> # foobar
        >>> x = 0
        >>> x / 0
        >>> # bazbiz
        ''')
    self = core.DocTest(docsrc=docsrc, lineno=0)
    self._parse()
    assert len(self._parts) == 1
    result = self.run(on_error='return')
    assert not result['passed']

    assert self.failed_lineno() == 3


def test_mod_lineno():
    import ubelt as ub
    from os.path import join
    dpath = ub.ensure_app_cache_dir('xdoctest', 'testing')
    modpath = join(dpath, 'test_lineno.py')
    source = ub.codeblock(
        '''
        class Fun(object):  #1
            @property
            def test(self):
                """         # 4
                >>> a = 1
                >>> 1 / 0
                """
        ''')
    ub.writeto(modpath, source)
    from xdoctest import core
    doctests = list(core.module_doctestables(modpath))
    assert len(doctests) == 1
    self = doctests[0]

    print(self._parts[0])

    assert self.lineno == 4
    print(self.format_src())

    assert self.format_src().strip().startswith('5')

    with PythonPathContext(dpath):
        status = self.run(verbose=10, on_error='return')

    assert not status['passed']


def test_mod_globals():
    import ubelt as ub
    from os.path import join
    dpath = ub.ensure_app_cache_dir('xdoctest', 'testing')
    modpath = join(dpath, 'test_mod_globals.py')
    source = ub.codeblock(
        '''
        X = 10
        def test(self):
            """
            >>> X
            10
            """
        ''')
    ub.writeto(modpath, source)
    from xdoctest import core
    doctests = list(core.module_doctestables(modpath))
    assert len(doctests) == 1
    self = doctests[0]

    with PythonPathContext(dpath):
        status = self.run(verbose=0, on_error='return')
    assert status['passed']
    assert self.evaled_results[0] == '10'


def test_show_entire():
    import ubelt as ub
    from os.path import join
    dpath = ub.ensure_app_cache_dir('xdoctest', 'testing')
    modpath = join(dpath, 'test_show_entire.py')
    source = ub.codeblock(
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
    ub.writeto(modpath, source)
    from xdoctest import core

    # calldefs = core.module_calldefs(modpath)
    # docline = calldefs['foo'].doclineno
    # docstr = calldefs['foo'].docstr
    # all_parts = doctest_parser.DoctestParser().parse(docstr)
    # assert docline == 2

    doctests = list(core.module_doctestables(modpath))
    assert len(doctests) == 1
    self = doctests[0]
    print(self.lineno)
    print(self._parts[0].line_offset)
    print(self.format_src())
    assert self.format_src().strip().startswith('6')

    with PythonPathContext(dpath):
        status = self.run(verbose=0, on_error='return')
    assert not status['passed']

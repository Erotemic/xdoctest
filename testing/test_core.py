
def test_failure():
    import ubelt as ub
    from xdoctest import core
    string = ub.codeblock(
        '''
        >>> i = 0
        >>> 0 / i
        2
        ''')
    self = core.DocTest('<testmod>', '<testfunc>',  docsrc=string, lineno=1000)
    self._parse()
    try:
        self.run(on_error='raise')
    except ZeroDivisionError as ex:
        pass
    else:
        raise AssertionError('should have gotten zero division')

    result = self.run(on_error='record')
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
        !!1 >>> i = 0
        !!2 >>> 0 / i
        !!  2
        ''').replace('!', ' ')
    self = core.DocTest('<test>', '<test>',  docsrc=string)
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
        7
        ''')
    self = core.DocTest('<test>', '<test>',  docsrc=docsrc)
    self._parse()
    p1, p2 = self._parts

    # test_globals = {}
    # code1 = compile(p1.source, '<string>', 'exec')
    # exec(code1, test_globals)
    # code2 = compile(p2.source, '<string>', 'eval')
    # result = eval(code2, test_globals)
    self.run()

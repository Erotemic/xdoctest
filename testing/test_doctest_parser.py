
def testdata():
    import ubelt as ub
    from xdoctest import doctest_parser
    string = '''
            text
            >>> dsrc()
            want

                >>> dsrc()
                >>> cont(
                ... a=b)
                ... dsrc
                >>> dsrc():
                ...     a
                ...     b = """
                        multiline
                        """
                want

            text
            ... still text
            >>> "now its a doctest"

            text
    '''
    string = ub.codeblock(string)
    self = doctest_parser.DoctestParser()
    self._label_docsrc_lines(string)

    self.parse(string)

    string = ub.codeblock(
        '''
            .. doctest::

                >>> print(
                ...    "Hi\\n\\nByé")
                Hi
                ...
                Byé
                >>> 1/0  # Byé
                1
        ''')
    import doctest
    self2 = doctest_parser.DoctestParser()
    self1 = doctest.DocTestParser()
    self2._label_docsrc_lines(string)

    string = ub.codeblock(
        """
        .. doctest::

            >>> '''
                multiline strings are now kosher
                '''
            multiline strings are now kosher
        """)

    string = ub.codeblock(
        """
        .. doctest::

            >>> x = y
            ... foo = bar
        """)

    string = ub.codeblock(
        '''
        text-line-1
        text-line-2
        text-line-3
        text-line-4
        text-line-5
        text-line-6
        text-line-7
        text-line-8
        text-line-9
        text-line-10
        text-line-11
        >>> 1 + 1
        3

        text-line-after
        ''')

    string = ub.codeblock(
        """
        >>> '''
            multiline strings are now kosher
            '''.strip()
        'multiline strings are now kosher'

        >>> '''
            double multiline string
            '''.strip()
        ...
        >>> '''
            double multiline string
            '''.strip()
        'double multiline string'
        """)

    import doctest
    import ubelt as ub
    self1 = doctest.DocTestParser()
    self2 = doctest_parser.DoctestParser()
    self2._label_docsrc_lines(string)
    print('\n==== PARSER2 ====')
    for x, o in enumerate(self2.parse(string)):
        print('----')
        print(x)
        if not isinstance(o, str):
            print(ub.repr2(o.__dict__, sv=True))
            # print('o.source = {!r}'.format(o.source))
            # print('o.want = {!r}'.format(o.want))
        else:
            print('o = {!r}'.format(o))
    print('\n==== PARSER1 ====')
    for x, o in enumerate(self1.parse(string)):
        print('----')
        print(x)
        if not isinstance(o, str):
            print(ub.repr2(o.__dict__))
            # print('o.source = {!r}'.format(o.source))
            # print('o.want = {!r}'.format(o.want))
        else:
            print('o = {!r}'.format(o))

    string = ub.codeblock(
        """
        .. doctest::

            >>> '''
                multiline strings are now kosher
                '''
            multiline strings are now kosher
        """)

    string = ub.codeblock(
        '''
        >>> import os
        >>> os.environ["HELLO"]
        'WORLD'
        ''')
    self = doctest_parser.DoctestParser()
    self._label_docsrc_lines(string)
    ex = self.parse(string)[0]

    outputs = self2.parse(string)
    print('outputs = {!r}'.format(outputs))
    for o in outputs:
        if not isinstance(o, str):
            e = o
            print('e.source = {!r}'.format(e.source))
            print('e.want = {!r}'.format(e.want))

    source = ub.codeblock(
            '''
            a = b; b = c
            def foo():
                pass
                pass
            try:
                a = b
            except Exception as ex:
                pass
            else:
                pass
            class X:
                def foo():
                    pass
            ''')
    import ast
    pt = ast.parse(source)
    ps1_linenos = sorted({node.lineno for node in pt.body})


def test_final_eval_exec():
    """
    Ensure that if the line before a want is able to be evaled, it is so we can
    compare its value to the want value.
    """
    import ubelt as ub
    from xdoctest import doctest_parser
    string = ub.codeblock(
        '''
        >>> x = 2
        >>> x + 1
        1
        ''')
    self = doctest_parser.DoctestParser()
    parts = self.parse(string)
    assert [p.use_eval for p in parts] == [False, True]

    string = ub.codeblock(
        '''
        >>> x = 2
        >>> x + 1
        ''')
    self = doctest_parser.DoctestParser()
    parts = self.parse(string)
    assert [p.use_eval for p in parts] == [False]

    string = ub.codeblock(
        r'''
        >>> x = 2
        >>> x += 3
        >>> """
        ... foobar
        ... """
        '\nfoobar\n'
        ''')
    self = doctest_parser.DoctestParser()
    parts = self.parse(string)
    assert [p.use_eval for p in parts] == [False, True]

    string = ub.codeblock(
        r'''
        >>> x = 2
        >>> x += 3
        >>> print('foo')
        foo
        ''')
    self = doctest_parser.DoctestParser()
    parts = self.parse(string)
    assert [p.use_eval for p in parts] == [False, True]

    string = ub.codeblock(
        r'''
        >>> i = 0
        >>> 0 / i
        2
        ''')
    self = doctest_parser.DoctestParser()
    parts = self.parse(string)
    assert [p.use_eval for p in parts] == [False, True]


def test_label_lines():
    import ubelt as ub
    from xdoctest import doctest_parser
    string = ub.codeblock(
        r'''
        >>> i = 0
        >>> 0 / i
        2
        ''')
    self = doctest_parser.DoctestParser()
    labeled = self._label_docsrc_lines(string)
    assert labeled == [
        ('dsrc', '>>> i = 0'),
        ('dsrc', '>>> 0 / i'),
        ('want', '2')
    ]

    string = '''
            text
            >>> dsrc()
            want

                >>> dsrc()
                >>> cont(
                ... a=b)
                ... dsrc
                >>> dsrc():
                ...     a
                ...     b = """
                        multiline
                        """
                want

            text
            ... still text
            >>> "now its a doctest"

            text
    '''
    self = doctest_parser.DoctestParser()
    labeled = self._label_docsrc_lines(string)
    assert labeled == [
        ('text', ''),
        ('text', '        text'),
        ('dsrc', '        >>> dsrc()'),
        ('want', '        want'),
        ('text', ''),
        ('dsrc', '            >>> dsrc()'),
        ('dsrc', '            >>> cont('),
        ('dsrc', '            ... a=b)'),
        ('dsrc', '            ... dsrc'),
        ('dsrc', '            >>> dsrc():'),
        ('dsrc', '            ...     a'),
        ('dsrc', '            ...     b = """'),
        ('dsrc', '                    multiline'),
        ('dsrc', '                    """'),
        ('want', '            want'),
        ('text', ''),
        ('text', '        text'),
        ('text', '        ... still text'),
        ('dsrc', '        >>> "now its a doctest"'),
        ('text', ''),
        ('text', '        text'),
    ]


def test_ps1_linenos():
    """
    Test we can find the line numbers for every "evaluatable" statement
    """
    import ubelt as ub
    from xdoctest import doctest_parser
    source_lines = ub.codeblock(
        '''
        >>> x = 2
        >>> x + 1
        1
        ''').split('\n')[:-1]
    self = doctest_parser.DoctestParser()
    line_indent = 0
    linenos, eval_final = self._locate_ps1_linenos(source_lines, line_indent)
    assert eval_final
    assert linenos == [0, 1]

    source_lines = ub.codeblock(
        '''
        >>> x = """
            x = 2
            """
        >>> print(x.strip() + '1')
        x = 21
        ''').split('\n')[:-1]
    self = doctest_parser.DoctestParser()
    line_indent = 0
    linenos, eval_final = self._locate_ps1_linenos(source_lines, line_indent)
    assert eval_final
    assert linenos == [0, 3]

    source_lines = ub.codeblock(
        '''
        >>> x = """
            x = 2
            """
        >>> y = (x.strip() + '1')
        'x = 21'
        ''').split('\n')[:-1]
    self = doctest_parser.DoctestParser()
    line_indent = 0
    linenos, eval_final = self._locate_ps1_linenos(source_lines, line_indent)
    assert eval_final
    assert linenos == [0, 3]

    source_lines = ub.codeblock(
        '''
        >>> x = """
            x = 2
            """
        >>> def foo():
        ...     return 5
        >>> ms1 = """
        ... multistring2
        ... multistring2
        ... """
        >>> ms2 = """
        ... multistring2
        ... multistring2
        ... """
        >>> x = sum([
        >>>     foo()
        >>> ])
        >>> y = len(ms1) + len(ms2)
        >>> z = (
        >>>     x + y
        >>> )
        >>> z
        59
        ''').split('\n')[:-1]
    self = doctest_parser.DoctestParser()
    line_indent = 0
    linenos, eval_final = self._locate_ps1_linenos(source_lines, line_indent)
    assert eval_final
    assert linenos == [0, 3, 5, 9, 13, 16, 17, 20]


def test_retain_source():
    import ubelt as ub
    from xdoctest import doctest_parser
    source = ub.codeblock(
        '''
        >>> x = 2
        >>> print("foo")
        foo
        ''')
    source_lines = source.split('\n')[:-1]
    self = doctest_parser.DoctestParser()
    line_indent = 0
    linenos, eval_final = self._locate_ps1_linenos(source_lines, line_indent)
    assert eval_final
    assert linenos == [0, 1]
    p1, p2 = self.parse(source)
    assert p1.source == 'x = 2'
    assert p2.source == 'print("foo")'


def testdata():
    import ubelt as ub
    from doctest2 import doctest_parser
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



def demodata():
    from xdoctest import utils, parser
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
    string = utils.codeblock(string)
    self = parser.DoctestParser()
    self._label_docsrc_lines(string)

    self.parse(string)

    string = utils.codeblock(
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
    self2 = parser.DoctestParser()
    self1 = doctest.DocTestParser()
    self2._label_docsrc_lines(string)

    string = utils.codeblock(
        """
        .. doctest::

            >>> '''
                multiline strings are now kosher
                '''
            multiline strings are now kosher
        """)

    string = utils.codeblock(
        """
        .. doctest::

            >>> x = y
            ... foo = bar
        """)

    string = utils.codeblock(
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

    string = utils.codeblock(
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
    self2 = parser.DoctestParser()
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

    string = utils.codeblock(
        """
        .. doctest::

            >>> '''
                multiline strings are now kosher
                '''
            multiline strings are now kosher
        """)

    string = utils.codeblock(
        '''
        >>> import os
        >>> os.environ["HELLO"]
        'WORLD'
        ''')
    self = parser.DoctestParser()
    self._label_docsrc_lines(string)
    ex = self.parse(string)[0]

    parts = self2.parse(string)
    print('parts = {!r}'.format(parts))
    for o in parts:
        if not isinstance(o, str):
            e = o
            print('e.source = {!r}'.format(e.source))
            print('e.want = {!r}'.format(e.want))

    source = utils.codeblock(
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

# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import pytest
from xdoctest import parser
from xdoctest import utils
from xdoctest import exceptions


def test_final_eval_exec():
    """
    Ensure that if the line before a want is able to be evaled, it is so we can
    compare its value to the want value.

    CommandLine:
        xdoctest -m ~/code/xdoctest/testing/test_parser.py test_final_eval_exec
    """
    string = utils.codeblock(
        '''
        >>> x = 2
        >>> x + 1
        1
        ''')
    self = parser.DoctestParser()
    parts = self.parse(string)
    DEBUG = 0
    if DEBUG:
        print(string)
        print([p.compile_mode for p in parts])
    assert [p.compile_mode for p in parts] == ['exec', 'eval']

    string = utils.codeblock(
        '''
        >>> x = 2
        >>> x + 1
        ''')
    self = parser.DoctestParser()
    parts = self.parse(string)
    if DEBUG:
        print(string)
        print([p.compile_mode for p in parts])
    assert [p.compile_mode for p in parts] == ['exec']

    string = utils.codeblock(
        r'''
        >>> x = 2
        >>> x += 3
        >>> """
        ... foobar
        ... """
        '\nfoobar\n'
        ''')
    self = parser.DoctestParser()
    parts = self.parse(string)
    if DEBUG:
        print(string)
        print([p.compile_mode for p in parts])
    assert [p.compile_mode for p in parts] == ['exec', 'single']

    string = utils.codeblock(
        r'''
        >>> i = 0
        >>> 0 / i
        2
        ''')
    self = parser.DoctestParser()
    parts = self.parse(string)
    if DEBUG:
        print(string)
        print([p.compile_mode for p in parts])
    assert [p.compile_mode for p in parts] == ['exec', 'eval']

    string = utils.codeblock(
        r'''
        >>> if True:
        ...     2
        2
        ''')
    self = parser.DoctestParser()
    parts = self.parse(string)
    if DEBUG:
        print(string)
        print([p.compile_mode for p in parts])
    assert [p.compile_mode for p in parts] == ['single']


def test_compile_mode_print():
    string = utils.codeblock(
        r'''
        >>> x = 2
        >>> x += 3
        >>> print('foo')
        foo
        ''')
    self = parser.DoctestParser()
    parts = self.parse(string)
    assert [p.compile_mode for p in parts] == ['exec', 'eval']


def test_label_lines():
    string = utils.codeblock(
        r'''
        >>> i = 0
        >>> 0 / i
        2
        ''')
    self = parser.DoctestParser()
    labeled = self._label_docsrc_lines(string)
    assert labeled == [
        ('dsrc', '>>> i = 0'),
        ('dsrc', '>>> 0 / i'),
        ('want', '2')
    ]


def test_label_indented_lines():
    string = '''
            text
            >>> dsrc1()
            want

                >>> dsrc2()
                >>> cont(
                ... a=b)
                ... dsrc
                >>> dsrc3():
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
    self = parser.DoctestParser()
    labeled = self._label_docsrc_lines(string)
    # import sys
    # print('EXIT NOW')
    # sys.exit(1)
    expected = [
        ('text', ''),
        ('text', '            text'),
        ('dsrc', '            >>> dsrc1()'),
        ('want', '            want'),
        ('text', ''),
        ('dsrc', '                >>> dsrc2()'),
        ('dsrc', '                >>> cont('),
        ('dcnt', '                ... a=b)'),
        ('dcnt', '                ... dsrc'),
        ('dsrc', '                >>> dsrc3():'),
        ('dcnt', '                ...     a'),
        ('dcnt', '                ...     b = """'),
        ('dcnt', '                        multiline'),
        ('dcnt', '                        """'),
        ('want', '                want'),
        ('text', ''),
        ('text', '            text'),
        ('text', '            ... still text'),
        ('dsrc', '            >>> "now its a doctest"'),
        ('text', ''),
        ('text', '            text'),
        ('text', '    '),    # FIXME: weird that this space has an indent
    ]
    if labeled != expected:
        try:
            import ubelt as ub
            import itertools as it
            for got, want in it.zip_longest(labeled, expected):
                if got != want:
                    print(utils.color_text('GOT  = {!r}'.format(got), 'red'))
                    print(utils.color_text('WANT = {!r}'.format(want), 'blue'))
                else:
                    print('PASS = {!r}'.format(got))
        except ImportError:
            pass
        raise AssertionError
    assert labeled == expected


def test_ps1_linenos_1():
    """
    Test we can find the line numbers for every "evaluatable" statement
    """
    source_lines = utils.codeblock(
        '''
        >>> x = 2
        >>> x + 1
        1
        ''').split('\n')[:-1]
    self = parser.DoctestParser()
    linenos, eval_final = self._locate_ps1_linenos(source_lines)
    assert eval_final
    assert linenos == [0, 1]


def test_ps1_linenos_2():
    source_lines = utils.codeblock(
        '''
        >>> x = """
            x = 2
            """
        >>> print(x.strip() + '1')
        x = 21
        ''').split('\n')[:-1]
    self = parser.DoctestParser()
    linenos, eval_final = self._locate_ps1_linenos(source_lines)
    assert eval_final
    assert linenos == [0, 3]


def test_ps1_linenos_3():
    source_lines = utils.codeblock(
        '''
        >>> x = """
            x = 2
            """
        >>> y = (x.strip() + '1')
        'x = 21'
        ''').split('\n')[:-1]
    self = parser.DoctestParser()
    linenos, eval_final = self._locate_ps1_linenos(source_lines)
    assert not eval_final
    assert linenos == [0, 3]


def test_ps1_linenos_4():
    source_lines = utils.codeblock(
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
    self = parser.DoctestParser()
    linenos, eval_final = self._locate_ps1_linenos(source_lines)
    assert eval_final
    assert linenos == [0, 3, 5, 9, 13, 16, 17, 20]


def test_retain_source():
    """
    """
    source = utils.codeblock(
        '''
        >>> x = 2
        >>> print("foo")
        foo
        ''')
    source_lines = source.split('\n')[:-1]
    self = parser.DoctestParser()
    linenos, eval_final = self._locate_ps1_linenos(source_lines)
    assert eval_final
    assert linenos == [0, 1]
    p1, p2 = self.parse(source)
    assert p1.source == 'x = 2'
    assert p2.source == 'print("foo")'


def test_package_string_tup():
    """
    pytest testing/test_parser.py::test_package_string_tup
    """
    raw_source_lines = ['>>> "string"']
    raw_want_lines = ['string']
    self = parser.DoctestParser()
    parts = list(self._package_chunk(raw_source_lines, raw_want_lines))
    assert len(parts) == 1, 'should only want one string'


def test_simulate_repl():
    """
    pytest testing/test_parser.py::test_package_string_tup
    """
    string = utils.codeblock(
        '''
        >>> x = 1
        >>> x = 2
        >>> x = 3
        ''')
    self = parser.DoctestParser()
    self.simulate_repl = False
    assert len(self.parse(string)) == 1
    self.simulate_repl = True
    assert len(self.parse(string)) == 3


def test_parse_multi_want():
    string = utils.codeblock(
        '''
        >>> x = 2
        >>> x
        2
        >>> 'string'
        'string'
        >>> print('string')
        string
        ''')
    self = parser.DoctestParser()
    parts = self.parse(string)

    self._label_docsrc_lines(string)
    assert parts[2].source == "'string'"
    assert len(parts) == 4


def test_parse_eval_nowant():
    string = utils.codeblock(
        '''
        >>> a = 1
        >>> 1 / 0
        ''')
    self = parser.DoctestParser()
    parts = self.parse(string)
    raw_source_lines = string.split('\n')[:]
    ps1_linenos, eval_final = self._locate_ps1_linenos(raw_source_lines)
    assert ps1_linenos == [0, 1]
    assert eval_final
    # Only one part because there is no want
    assert len(parts) == 1


def test_parse_eval_single_want():
    string = utils.codeblock(
        '''
        >>> a = 1
        >>> 1 / 0
        We have a want
        ''')
    self = parser.DoctestParser()
    parts = self.parse(string)
    raw_source_lines = string.split('\n')[:-1]
    ps1_linenos, eval_final = self._locate_ps1_linenos(raw_source_lines)
    assert ps1_linenos == [0, 1]
    assert eval_final
    # Only one part because there is no want
    assert len(parts) == 2


def test_parse_comment():
    string = utils.codeblock(
        '''
        >>> # nothing
        ''')
    self = parser.DoctestParser()
    labeled = self._label_docsrc_lines(string)
    assert labeled == [('dsrc', '>>> # nothing')]
    source_lines = string.split('\n')[:]
    linenos, eval_final = self._locate_ps1_linenos(source_lines)
    parts = self.parse(string)
    assert parts[0].source.strip().startswith('#')


def test_text_after_want():
    string = utils.codeblock('''
        Example:
            >>> dsrc()
            want
        just some test
    ''')
    self = parser.DoctestParser()
    labeled = self._label_docsrc_lines(string)
    expected = [
        ('text', 'Example:'),
        ('dsrc', '    >>> dsrc()'),
        ('want', '    want'),
        ('text', 'just some test'),
    ]
    assert labeled == expected


def test_want_ellipse_with_space():
    string = utils.codeblock('''
        Example:
            >>> dsrc()
            ...
    ''')
    # Add an extra space after the ellipses to be clear what we are testing
    # and because my editor automatically removes it when I try to save the
    # file ¯\_(ツ)_/¯
    string = string + ' '
    self = parser.DoctestParser()
    labeled = self._label_docsrc_lines(string)
    expected = [
        ('text', 'Example:'),
        ('dsrc', '    >>> dsrc()'),
        ('want', '    ... '),
    ]
    assert labeled == expected


def test_syntax_error():
    string = utils.codeblock('''
        Example:
            >>> 03 = dsrc()
    ''')
    self = parser.DoctestParser()
    with pytest.raises(exceptions.DoctestParseError):
        self.parse(string)


def test_nonbalanced_statement():
    """
    xdoctest ~/code/xdoctest/testing/test_parser.py test_nonbalanced_statement

    from xdoctest import static_analysis as static
    lines = ['x = [']
    static.is_balanced_statement(lines, only_tokens=True)
    """
    string = utils.codeblock(
        '''
        >>> x = [
        # ] this braket is to make my editor happy and is does not effect the test
        ''').splitlines()[0]

    self = parser.DoctestParser()
    with pytest.raises(exceptions.DoctestParseError) as exc_info:
        self.parse(string)
    msg = exc_info.value.orig_ex.msg.lower()
    assert msg.startswith('ill-formed doctest'.lower())


def test_bad_indent():
    """
    CommandLine:
        python testing/test_parser.py test_bad_indent
    """
    string = utils.codeblock(
        '''
        Example:
            >>> x = [
        # ] bad want indent
        ''')

    self = parser.DoctestParser()
    with pytest.raises(exceptions.DoctestParseError) as exc_info:
        self.parse(string)
    msg = exc_info.value.orig_ex.msg.lower()
    assert msg.startswith('Bad indentation in doctest'.lower())


def test_part_nice_no_lineoff():
    from xdoctest import doctest_part
    self = doctest_part.DoctestPart([], [], None)
    assert str(self) == '<DoctestPart(src="", want=None)>'


def test_repl_oneline():
    string = utils.codeblock(
        '''
        >>> x = 1
        ''')
    self = parser.DoctestParser(simulate_repl=True)
    parts = self.parse(string)
    assert [p.source for p in parts] == ['x = 1']


def test_repl_twoline():
    string = utils.codeblock(
        '''
        >>> x = 1
        >>> x = 2
        ''')
    self = parser.DoctestParser(simulate_repl=True)
    parts = self.parse(string)
    assert [p.source for p in parts] == ['x = 1', 'x = 2']


def test_repl_comment_in_string():
    source_lines = ['>>> x = """', '    # comment in a string', '    """']
    self = parser.DoctestParser()
    assert self._locate_ps1_linenos(source_lines) == ([0], False)

    source_lines = [
        '>>> x = """',
        '    # comment in a string',
        '    """',
        '>>> x = """',
        '    # comment in a string',
        '    """',
    ]
    self = parser.DoctestParser()
    assert self._locate_ps1_linenos(source_lines) == ([0, 3], False)


def test_inline_directive():
    """
        python ~/code/xdoctest/testing/test_parser.py test_inline_directive
    """
    string = utils.codeblock(
        '''
        >>> # doctest: +SKIP
        >>> func1(*
        >>>    [i for i in range(10)])
        >>> # not a directive
        >>> func2(  # not a directive
        >>>    a=b
        >>>    )
        >>> func3()  # xdoctest: +SKIP
        >>> func4()
        want1
        >>> func5()  # xdoctest: +SKIP
        want1
        >>> # xdoctest: +SKIP
        >>> func6()
        >>> func7(a=b,
        >>>            c=d) # xdoctest: +SKIP
        >>> # xdoctest: +SKIP
        >>> func8(' # doctest: not a directive')
        >>> func9("""
                  # doctest: still not a directive
                  """)
        finalwant
        ''')
    # source_lines = string.splitlines()
    self = parser.DoctestParser()
    # ps1_linenos = self._locate_ps1_linenos(source_lines)[0]
    # print(ps1_linenos)
    # [0, 1, 3, 4, 7, 8, 10, 11, 12]
    # assert ps1_linenos == [0, 2, 5, 6, 8, 9, 10]
    parts = self.parse(string)
    # assert len(parts) ==
    for part in parts:
        print('----')
        print(part.source)
        print('----')
    try:
        print(parts)
    except ImportError:
        pass
    # TODO: finsh me


def test_block_directive_nowant1():
    """
        python ~/code/xdoctest/testing/test_parser.py test_block_directive_nowant1
    """
    string = utils.codeblock(
        '''
        >>> # doctest: +SKIP
        >>> func1()
        >>> func2()
        ''')
    # source_lines = string.splitlines()
    self = parser.DoctestParser()
    # ps1_linenos = self._locate_ps1_linenos(source_lines)[0]
    parts = self.parse(string)
    print('----')
    for part in parts:
        print(part.source)
        print('----')
    try:
        print(parts)
    except ImportError:
        pass
    assert len(parts) == 1


def test_block_directive_nowant2():
    """
        python ~/code/xdoctest/testing/test_parser.py test_block_directive_nowant
    """
    string = utils.codeblock(
        '''
        >>> # doctest: +SKIP
        >>> func1()
        >>> func2()
        >>> # doctest: +SKIP
        >>> func1()
        >>> func2()
        ''')
    # source_lines = string.splitlines()
    self = parser.DoctestParser()
    # ps1_linenos = self._locate_ps1_linenos(source_lines)[0]
    parts = self.parse(string)
    # TODO: finsh me
    assert len(parts) == 2


def test_block_directive_want1_assign():
    """
        python ~/code/xdoctest/testing/test_parser.py test_block_directive_want1
    """
    string = utils.codeblock(
        '''
        >>> # doctest: +SKIP
        >>> func1()
        >>> _ = func2()  # assign this line so we dont break it off for eval
        want
        ''')
    # source_lines = string.splitlines()
    self = parser.DoctestParser()
    # ps1_linenos = self._locate_ps1_linenos(source_lines)[0]
    parts = self.parse(string)
    print('----')
    for part in parts:
        print(part.source)
        print('----')
    try:
        print(parts)
    except ImportError:
        pass
    assert len(parts) == 1


def test_block_directive_want1_eval():
    """
        python ~/code/xdoctest/testing/test_parser.py test_block_directive_want1
    """
    string = utils.codeblock(
        '''
        >>> # doctest: +SKIP
        >>> func1()
        >>> func2()  # eval this line so it is broken off
        want
        ''')
    source_lines = string.splitlines()
    self = parser.DoctestParser()
    ps1_linenos = self._locate_ps1_linenos(source_lines)[0]
    parts = self.parse(string)
    assert len(parts) == 2


def test_block_directive_want2_assign():
    """
        python ~/code/xdoctest/testing/test_parser.py test_block_directive_want2
    """
    string = utils.codeblock(
        '''
        >>> func1()
        >>> # doctest: +SKIP
        >>> func2()
        >>> _ = func3()
        want
        ''')
    source_lines = string.splitlines()
    self = parser.DoctestParser()
    ps1_linenos = self._locate_ps1_linenos(source_lines)[0]
    parts = self.parse(string)
    assert len(parts) == 2


def test_block_directive_want2_eval():
    """
        python ~/code/xdoctest/testing/test_parser.py test_block_directive_want2_eval
    """
    string = utils.codeblock(
        '''
        >>> func1()
        >>> # doctest: +SKIP
        >>> func2()
        >>> func3()
        want
        ''')
    source_lines = string.splitlines()
    self = parser.DoctestParser()
    ps1_linenos = self._locate_ps1_linenos(source_lines)[0]
    parts = self.parse(string)
    print('----')
    for part in parts:
        print(part.source)
        print('----')
    try:
        print(parts)
    except ImportError:
        pass
    assert len(parts) == 3


def test_block_directive_want2_eval2():
    """
        python ~/code/xdoctest/testing/test_parser.py test_block_directive_want2_eval
    """
    string = utils.codeblock(
        '''
        >>> func1()
        >>> func1()
        >>> # doctest: +SKIP
        >>> func2()
        >>> func2()
        >>> # doctest: +SKIP
        >>> func3()
        >>> func3()
        >>> func3()
        >>> func4()
        want
        ''')
    source_lines = string.splitlines()
    self = parser.DoctestParser()
    ps1_linenos = self._locate_ps1_linenos(source_lines)[0]
    parts = self.parse(string)
    assert len(parts) == 4


def test_gh_issue_25_parsing_failure():
    string = utils.codeblock(
        '''
        >>> _, o = 0, 1
        >>> A = B = C = D = 1
        >>> cc_mask = [        # Y
        >>>     [ _, _, _, o, _, _, ],  # 0
        >>>     [ _, _, o, o, o, _, ],  # 1
        >>>     [ _, o, o, o, o, o, ],  # 2
        >>>     [ o, o, o, o, o, _, ],  # 3
        >>>     [ _, o, o, o, _, _, ],  # 4
        >>>     [ _, _, o, o, _, _, ],  # 5
        >>> # X:  0  1  2  3  4  5  6
        >>> ]
        >>> # a regular comment
        >>> print(cc_mask)
        ''')
    source_lines = string.splitlines()
    self = parser.DoctestParser()
    ps1_linenos = self._locate_ps1_linenos(source_lines)[0]
    assert ps1_linenos ==  [0, 1, 2, 11, 12]
    parts = self.parse(string)
    assert len(parts) == 1


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdoctest/testing/test_parser.py --help
        python ~/code/xdoctest/testing/test_parser.py test_inline_directive
        python ~/code/xdoctest/testing/test_parser.py zero-all
        python ~/code/xdoctest/testing/test_parser.py test_gh_issue_25_parsing_failure
        pytest testing/test_parser.py -vv
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from xdoctest import parser
from xdoctest import utils


def test_final_eval_exec():
    """
    Ensure that if the line before a want is able to be evaled, it is so we can
    compare its value to the want value.
    """
    string = utils.codeblock(
        '''
        >>> x = 2
        >>> x + 1
        1
        ''')
    self = parser.DoctestParser()
    parts = self.parse(string)
    assert [p.use_eval for p in parts] == [False, True]

    string = utils.codeblock(
        '''
        >>> x = 2
        >>> x + 1
        ''')
    self = parser.DoctestParser()
    parts = self.parse(string)
    assert [p.use_eval for p in parts] == [False]

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
    assert [p.use_eval for p in parts] == [False, True]

    string = utils.codeblock(
        r'''
        >>> x = 2
        >>> x += 3
        >>> print('foo')
        foo
        ''')
    self = parser.DoctestParser()
    parts = self.parse(string)
    assert [p.use_eval for p in parts] == [False, True]

    string = utils.codeblock(
        r'''
        >>> i = 0
        >>> 0 / i
        2
        ''')
    self = parser.DoctestParser()
    parts = self.parse(string)
    assert [p.use_eval for p in parts] == [False, True]


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
    self = parser.DoctestParser()
    labeled = self._label_docsrc_lines(string)
    expected = [
        ('text', ''),
        ('text', '            text'),
        ('dsrc', '            >>> dsrc()'),
        ('want', '            want'),
        ('text', ''),
        ('dsrc', '                >>> dsrc()'),
        ('dsrc', '                >>> cont('),
        ('dsrc', '                ... a=b)'),
        ('dsrc', '                ... dsrc'),
        ('dsrc', '                >>> dsrc():'),
        ('dsrc', '                ...     a'),
        ('dsrc', '                ...     b = """'),
        ('dsrc', '                        multiline'),
        ('dsrc', '                        """'),
        ('want', '                want'),
        ('text', ''),
        ('text', '            text'),
        ('text', '            ... still text'),
        ('dsrc', '            >>> "now its a doctest"'),
        ('text', ''),
        ('text', '            text'),
        ('text', '    '),    # FIXME: weird that this space has an indent
    ]
    # print('labeled = ' + ub.repr2(labeled))
    # print('expected = ' + ub.repr2(expected))
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

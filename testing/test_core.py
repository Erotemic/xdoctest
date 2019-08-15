# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from os.path import join
import xdoctest
from xdoctest import core
from xdoctest import utils


def _test_status(docstr):
    docstr = utils.codeblock(docstr)
    try:
        temp = utils.util_misc.TempDoctest(docstr=docstr)
    except Exception:
        raise
        # pytest seems to load an older version of xdoctest for some reason
        import xdoctest
        import inspect
        print('xdoctest.__version__ = {!r}'.format(xdoctest.__version__))
        print('utils = {!r}'.format(utils))
        print('utils.util_misc = {!r}'.format(utils.util_misc))
        print('utils.TempDoctest = {!r}'.format(utils.TempDoctest))
        print(inspect.getargspec(utils.TempDoctest))
        raise
    doctests = list(core.parse_doctestables(temp.modpath))
    status = doctests[0].run(verbose=0, on_error='return')
    return status


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
    """
    pytest testing/test_core.py::test_show_entire
    """
    temp = utils.TempDir()
    dpath = temp.ensure()
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

    src_offset = self.format_src(offset_linenos=True).strip()
    src_nooffset = self.format_src(offset_linenos=False).strip()

    assert src_offset[:4].startswith('6')
    assert src_nooffset[:4].startswith('1')

    with utils.PythonPathContext(dpath):
        status = self.run(verbose=0, on_error='return')
    assert not status['passed']
    temp.cleanup()


def test_freeform_parse_lineno():
    """
        python ~/code/xdoctest/testing/test_core.py test_freeform_parse_lineno

    """
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
    doctests = list(core.parse_freeform_docstr_examples(docstr, lineno=1, asone=False))
    assert  [test.lineno for test in doctests] == [1, 4, 10, 14, 20]

    # This asserts if the lines are consecutive. Should we enforce this?
    # Perhaps its ok if they are not.
    for test in doctests:
        assert test._parts[0].line_offset == 0
        offset = 0
        for p in test._parts:
            assert p.line_offset == offset
            offset += p.n_lines

    doctests = list(core.parse_freeform_docstr_examples(docstr, lineno=1, asone=True))
    assert  [test.lineno for test in doctests] == [1]

    doctests = list(core.parse_google_docstr_examples(docstr, lineno=1))
    assert  [test.lineno for test in doctests] == [4, 10, 14]

    for test in doctests:
        test._parse()
        assert test._parts[0].line_offset == 0
        offset = 0
        for p in test._parts:
            assert p.line_offset == offset
            offset += p.n_lines


def test_collect_module_level():
    """
    pytest testing/test_core.py::test_collect_module_level -s -vv

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

    src_offset = self.format_src(offset_linenos=True).strip()
    src_nooffset = self.format_src(offset_linenos=False).strip()
    assert src_offset[:4].startswith('2')
    assert src_nooffset[:4].startswith('1')

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


def test_no_docstr():
    """
    CommandLine:
        python -m test_core test_no_docstr
    """
    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_no_docstr.py')
        source = utils.codeblock(
            '''
            def get_scales(kpts):
                """ Gets average scale (does not take into account elliptical shape """
                _scales = np.sqrt(get_sqrd_scales(kpts))
                return _scales
            ''')
        with open(modpath, 'w') as file:
            file.write(source)
        from xdoctest import core
        doctests = list(core.parse_doctestables(modpath, style='freeform'))
        assert len(doctests) == 0


def test_oneliner():
    """
    python ~/code/xdoctest/testing/test_core.py test_oneliner
    """
    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_oneliner.py')
        source = utils.codeblock(
            '''
            def foo():
                """
                >>> assert False, 'should fail'
                """
            ''')
        with open(modpath, 'w') as file:
            file.write(source)
        doctests = list(core.parse_doctestables(modpath))
        assert len(doctests) == 1
        print('doctests = {!r}'.format(doctests))
        import pytest
        with pytest.raises(AssertionError, match='should fail'):
            doctests[0].run()


def test_delayed_want_pass_cases():
    """
    The delayed want algorithm allows a want statement to match trailing
    unmatched stdout if it fails to directly match the most recent stdout.

    In more mathy terms let $w$ be the current "want", and let $g[-t:]$ be the
    trailing $t$ most recent "gots" captured from stdout. We say the "want"
    matches "got" if $w matches g[-t:] for t in range(1, n)$, where $n$ is the
    index of the last part with a success match.

    CommandLine:
        python ~/code/xdoctest/testing/test_core.py test_delayed_want_pass_cases
    """

    # Pass Case1:
    status = _test_status(
        """
        >>> print('some text')
        >>> print('more text')
        some text
        more text
        """)
    assert status['passed']

    # Pass Case2:
    status = _test_status(
        """
        >>> print('some text')
        some text
        >>> print('more text')
        more text
        """)
    assert status['passed']

    # Pass Case3: "its ok to only match more text and ignore some text"
    status = _test_status(
        """
        >>> print('some text')
        >>> print('more text')
        more text
        """)
    assert status['passed']


def test_delayed_want_fail_cases():
    """
    CommandLine:
        xdoctest -m ~/code/xdoctest/testing/test_core.py test_delayed_want_fail_cases
    """
    # Fail Case4: "more text has not been printed yet"
    status = _test_status(
        """
        >>> print('some text')
        some text
        more text
        >>> print('more text')
        """)
    assert not status['passed']

    # Fail Case5: cannot match "some text" more than once
    status = _test_status(
        """
        >>> print('some text')
        some text
        >>> print('more text')
        some text
        more text
        """)
    assert not status['passed']

    # Fail Case6: Because "more text" was matched, "some text" is forever
    # ignored
    status = _test_status(
        """
        >>> print('some text')
        >>> print('more text')
        more text
        >>> print('even more text')
        some text
        even more text
        """)
    assert not status['passed']

    # alternate case 6
    status = _test_status(
        """
        >>> print('some text')
        >>> print('more text')
        more text
        >>> print('even more text')
        some text
        more text
        even more text
        """)
    assert not status['passed']


def test_indented_grouping():
    """
    Initial changes in 0.10.0 broke parsing of some ubelt tests, check to
    ensure using `...` in indented blocks is ok (as long as there is no want
    string in the indented block).

    CommandLine:
        xdoctest -m ~/code/xdoctest/testing/test_core.py test_indented_grouping
    """
    from xdoctest.doctest_example import DocTest
    example = DocTest(
        utils.codeblock(r"""
        >>> from xdoctest.utils import codeblock
        >>> # Simulate an indented part of code
        >>> if True:
        >>>     # notice the indentation on this will be normal
        >>>     codeblock_version = codeblock(
        ...             '''
        ...             def foo():
        ...                 return 'bar'
        ...             '''
        ...         )
        >>>     # notice the indentation and newlines on this will be odd
        >>>     normal_version = ('''
        ...         def foo():
        ...             return 'bar'
        ...     ''')
        >>> assert normal_version != codeblock_version
        """))
    # print(example.format_src())
    status = example.run(verbose=0)
    assert status['passed']


def test_backwards_compat_eval_in_loop():
    """
    Test that changes in 0.10.0 fix backwards compatibility issue.

    CommandLine:
        xdoctest -m ~/code/xdoctest/testing/test_core.py test_backwards_compat_eval_in_loop
    """
    from xdoctest.doctest_example import DocTest
    example = DocTest(
        utils.codeblock(r"""
        >>> for i in range(2):
        ...     '%s' % i
        ...
        '0'
        '1'
        """))
    # print(example.format_src())
    status = example.run(verbose=0)
    assert status['passed']

    example = DocTest(
        utils.codeblock(r"""
        >>> for i in range(2):
        ...     '%s' % i
        '0'
        '1'
        """))
    status = example.run(verbose=0)
    assert status['passed']


def test_backwards_compat_indent_value():
    """
    CommandLine:
        xdoctest -m ~/code/xdoctest/testing/test_core.py test_backwards_compat_indent_value
    """
    from xdoctest.doctest_example import DocTest
    example = DocTest(
        utils.codeblock(r"""
        >>> b = 3
        >>> if True:
        ...     a = 1
        ...     isinstance(1, int)
        True
        """))
    status = example.run(verbose=0)
    assert status['passed']


if __name__ == '__main__':
    """
    CommandLine:
        export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/xdoctest/testing
        python ~/code/xdoctest/testing/test_core.py zero
        pytest testing/test_core.py -vv
    """
    import xdoctest  # NOQA
    xdoctest.doctest_module(__file__)

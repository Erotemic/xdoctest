# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from os.path import join
from xdoctest import core
from xdoctest import utils


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


if __name__ == '__main__':
    r"""
    CommandLine:
        export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/xdoctest/testing
        python ~/code/xdoctest/testing/test_core.py
        pytest testing/test_core.py -vv
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

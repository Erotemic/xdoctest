# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from xdoctest import static_analysis as static
from xdoctest import utils


def test_module_docstr():
    source = utils.codeblock(
        '''
        # comment
        """
        module level docstr
        """

        def foo():
            """ other docstr """
        ''')

    self = static.TopLevelVisitor.parse(source)
    assert '__doc__' in self.calldefs


def test_lineno():
    source = utils.codeblock(
        '''
        def foo():
            """ multiline 0-1-0 """
            def subfunc():
                pass
        def bar():
            """
            multiline 1-1-1
            """
            pass
        def baz():
            """ multiline 0-1-1
            """

        def biz():
            """
            multiline 1-1-0 """

        class Spam(object):
            """ multiline 0-2-1
            ---
            """
            def eggs():
                """ multiline 0-2-0
                ---"""
                pass
        ''')

    self = static.TopLevelVisitor.parse(source)
    calldefs = self.calldefs

    sourcelines = source.split('\n')

    for k, calldef in calldefs.items():
        line = sourcelines[calldef.lineno - 1]
        callname = calldef.callname
        # Ensure linenumbers correspond with start of func/class def
        assert callname.split('.')[-1] in line
        docsrc_lines = sourcelines[calldef.doclineno - 1:calldef.doclineno_end]
        # Ensure linenumbers correspond with start and end of doctest
        assert docsrc_lines[0].strip().startswith('"""')
        assert docsrc_lines[-1].strip().endswith('"""')


def test_mod_lineno2():
    source = utils.codeblock(
        '''
        class Fun(object):  #1
            @property
            def test(self):
                """         # 4
                >>> a = 1
                >>> 1 / 0
                """

        def nodec1(self):  # 9
            pass

        def nodec2(self,  # 12
                   x=y):
            """           # 14
            >>> d = 1
            """           # 16

        @decor             # 18
        def decor1(self):  # 19
            pass

        @decor()
        def decor2(self):
            pass

        @decor(
            foo=bar
        )
        def decor3(self):  # 29
            """
            >>> d = 3
            """

        @decor(
            foo=bar         # 35
        )                   # 36
        def decor4(self):   # 37
            ">>> print(1)"  # 38
        ''')
    # import ast
    from xdoctest.static_analysis import TopLevelVisitor
    # source_utf8 = source.encode('utf8')
    # pt = ast.parse(source_utf8)
    # node = pt.body[0].body[0]
    self = TopLevelVisitor.parse(source)

    calldefs = self.calldefs
    assert calldefs['Fun'].lineno == 1
    assert calldefs['Fun.test'].lineno == 3
    assert calldefs['Fun.test'].doclineno == 4
    assert calldefs['Fun.test'].doclineno_end == 7
    assert calldefs['nodec1'].doclineno is None
    assert calldefs['nodec2'].doclineno == 14
    assert calldefs['nodec2'].doclineno_end == 16
    assert calldefs['decor3'].doclineno == 30
    assert calldefs['decor3'].doclineno_end == 32
    assert calldefs['decor4'].doclineno == 38
    assert calldefs['decor4'].doclineno_end == 38


if __name__ == '__main__':
    """
    CommandLine:
        python -B %HOME%/code/xdoctest/testing/test_static.py all
        pytest ~/code/xdoctest/testing/test_static.py
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

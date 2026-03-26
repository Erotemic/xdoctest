import pytest
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
        '''
    )

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

        class Spam:
            """ multiline 0-2-1
            ---
            """
            def eggs():
                """ multiline 0-2-0
                ---"""
                pass
        '''
    )

    self = static.TopLevelVisitor.parse(source)
    calldefs = self.calldefs

    sourcelines = source.split('\n')

    for k, calldef in calldefs.items():
        line = sourcelines[calldef.lineno - 1]
        callname = calldef.callname
        # Ensure linenumbers correspond with start of func/class def
        assert callname.split('.')[-1] in line
        docsrc_lines = sourcelines[
            calldef.doclineno - 1 : calldef.doclineno_end
        ]
        # Ensure linenumbers correspond with start and end of doctest
        assert docsrc_lines[0].strip().startswith('"""')
        assert docsrc_lines[-1].strip().endswith('"""')


def test_mod_lineno2():
    source = utils.codeblock(
        '''
        class Fun:  #1
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
        '''
    )
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


def test_async_function_docstr_collection():
    source = utils.codeblock(
        '''
        async def b():
            """
            >>> b()
            2
            """
            return 1
        '''
    )

    self = static.TopLevelVisitor.parse(source)
    assert 'b' in self.calldefs
    assert self.calldefs['b'].doclineno == 2
    assert self.calldefs['b'].doclineno_end == 5


def test_parse_decorated_async_function_lineno():
    source = utils.codeblock(
        '''
        def deco(func):
            return func

        @deco
        async def foo():
            """
            Example:
                >>> 1 + 1
                2
            """
            return 42
        '''
    )

    modpath = 'test_parse_decorated_async_function_lineno.py'
    calldefs = static.parse_static_calldefs(
        source=source,
        fpath=modpath,
    )

    assert 'foo' in calldefs
    calldef = calldefs['foo']

    # Should point to the `async def foo():` line, not the decorator line.
    source_lines = source.splitlines()
    assert source_lines[calldef.lineno - 1].strip() == 'async def foo():'

    # And it should still extract the docstring normally.
    assert '>>> 1 + 1' in calldef.docstr


def test_parse_multi_decorated_async_function_lineno():
    source = utils.codeblock(
        '''
        def deco1(func):
            return func

        def deco2(func):
            return func

        @deco1
        @deco2
        async def foo():
            """
            Example:
                >>> 1 + 1
                2
            """
            return 42
        '''
    )

    calldefs = static.parse_static_calldefs(
        source=source,
        fpath='dummy.py',
    )
    calldef = calldefs['foo']

    source_lines = source.splitlines()
    assert source_lines[calldef.lineno - 1].strip() == 'async def foo():'
    assert '>>> 1 + 1' in calldef.docstr


@pytest.mark.parametrize(
    'case',
    [
        {
            'name': 'decorated_async_single',
            'source': '''
            def deco(func):
                return func

            @deco
            async def foo():
                """
                Example:
                    >>> 1 + 1
                    2
                """
                return 42
        ''',
            'callname': 'foo',
            'expect_line': 'async def foo():',
        },
        {
            'name': 'decorated_async_multiple',
            'source': '''
            def deco1(func):
                return func

            def deco2(func):
                return func

            @deco1
            @deco2
            async def foo():
                """
                Example:
                    >>> 1 + 1
                    2
                """
                return 42
        ''',
            'callname': 'foo',
            'expect_line': 'async def foo():',
        },
        {
            'name': 'decorated_async_with_args',
            'source': '''
            def deco(func):
                return func

            def deco_factory(*args, **kwargs):
                def wrap(func):
                    return func
                return wrap

            @deco_factory(arg=1)
            async def foo():
                """
                Example:
                    >>> 1 + 1
                    2
                """
                return 42
        ''',
            'callname': 'foo',
            'expect_line': 'async def foo():',
        },
        {
            'name': 'decorated_async_mixed',
            'source': '''
            def deco1(func):
                return func

            def deco2(*args, **kwargs):
                def wrap(func):
                    return func
                return wrap

            @deco1
            @deco2(arg=1)
            async def foo():
                """
                Example:
                    >>> 1 + 1
                    2
                """
                return 42
        ''',
            'callname': 'foo',
            'expect_line': 'async def foo():',
        },
        {
            'name': 'decorated_async_with_comment',
            'source': '''
            def deco1(func):
                return func

            def deco2(func):
                return func

            @deco1
            # comment between decorators
            @deco2
            async def foo():
                """
                Example:
                    >>> 1 + 1
                    2
                """
                return 42
        ''',
            'callname': 'foo',
            'expect_line': 'async def foo():',
        },
        {
            'name': 'decorated_async_multiline_signature',
            'source': '''
            def deco(func):
                return func

            @deco
            async def foo(
                    a, b,
                    c):
                """
                Example:
                    >>> 1 + 1
                    2
                """
                return 42
        ''',
            'callname': 'foo',
            'expect_line': 'async def foo(',
        },
        {
            'name': 'decorated_sync_and_async_together',
            'source': '''
            def deco(func):
                return func

            @deco
            def bar():
                """
                Example:
                    >>> "bar"
                    'bar'
                """
                return 'bar'

            @deco
            async def foo():
                """
                Example:
                    >>> 1 + 1
                    2
                """
                return 42
        ''',
            'callname': 'foo',
            'expect_line': 'async def foo():',
        },
        {
            'name': 'decorated_method_in_class',
            'source': '''
            def deco(func):
                return func

            class C:
                @classmethod
                @deco
                async def foo(cls):
                    """
                    Example:
                        >>> 1 + 1
                        2
                    """
                    return 42
        ''',
            'callname': 'C.foo',
            'expect_line': 'async def foo(cls):',
        },
        {
            'name': 'decorated_staticmethod_in_class',
            'source': '''
            def deco(func):
                return func

            class C:
                @staticmethod
                @deco
                async def foo():
                    """
                    Example:
                        >>> 1 + 1
                        2
                    """
                    return 42
        ''',
            'callname': 'C.foo',
            'expect_line': 'async def foo():',
        },
        {
            'name': 'decorated_async_after_module_docstring_and_blanks',
            'source': '''
            """
            module docstring
            """


            def deco(func):
                return func


            @deco
            async def foo():
                """
                Example:
                    >>> 1 + 1
                    2
                """
                return 42
        ''',
            'callname': 'foo',
            'expect_line': 'async def foo():',
        },
        {
            'name': 'decorated_async_non_ascii_prefix',
            'source': '''
            # café

            def deco(func):
                return func

            @deco
            async def foo():
                """
                Example:
                    >>> 1 + 1
                    2
                """
                return 42
        ''',
            'callname': 'foo',
            'expect_line': 'async def foo():',
        },
    ],
)
def test_parse_decorated_function_lineno_cases(case):
    source = utils.codeblock(case['source'])

    calldefs = static.parse_static_calldefs(
        source=source,
        fpath=case['name'] + '.py',
    )

    assert case['callname'] in calldefs, (
        'Missing calldef {!r} in case {!r}. Got keys={!r}'.format(
            case['callname'], case['name'], sorted(calldefs.keys())
        )
    )

    calldef = calldefs[case['callname']]
    source_lines = source.splitlines()

    got_line = source_lines[calldef.lineno - 1].strip()
    assert got_line == case['expect_line'], (
        'Wrong lineno for case={!r}. Expected line={!r}, got line={!r}, '
        'lineno={!r}'.format(
            case['name'], case['expect_line'], got_line, calldef.lineno
        )
    )

    assert '>>> 1 + 1' in calldef.docstr or '>>> "bar"' in calldef.docstr


if __name__ == '__main__':
    """
    CommandLine:
        python -B %HOME%/code/xdoctest/tests/test_static.py all
        pytest ~/code/xdoctest/tests/test_static.py
    """
    import xdoctest

    xdoctest.doctest_module(__file__)

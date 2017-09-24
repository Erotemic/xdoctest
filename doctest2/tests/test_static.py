
def test_lineno():
    from doctest2 import static_analysis as static
    import ubelt as ub
    source = ub.codeblock(
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
        docsrc_lines = sourcelines[calldef.doclineno - 1:calldef.doclineno_end - 1]
        # Ensure linenumbers correspond with start and end of doctest
        assert docsrc_lines[0].strip().startswith('"""')
        assert docsrc_lines[-1].strip().endswith('"""')

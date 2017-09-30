
def test_eval_expr_capture():
    import ubelt as ub
    from xdoctest import core

    docsrc = ub.codeblock(
        '''
        >>> x = 3
        >>> y = x + 2
        >>> y + 2
        7
        ''')
    self = core.DocTest('<test>', '<test>',  docsrc=docsrc)
    self._parse()
    p1, p2 = self._parts

    # test_globals = {}
    # code1 = compile(p1.source, '<string>', 'exec')
    # exec(code1, test_globals)
    # code2 = compile(p2.source, '<string>', 'eval')
    # result = eval(code2, test_globals)
    self.run()

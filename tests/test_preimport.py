# -*- coding: utf-8 -*-
from os.path import join
from xdoctest import utils


def test_preimport_skiped_on_disabled_module():
    """
    If our module has no enabled tests, pre-import should never run.
    """

    from xdoctest import runner
    import os

    source = utils.codeblock(
        '''
        raise Exception("DONT IMPORT ME!")


        def ima_function():
            """
            Example:
                >>> # xdoctest: +REQUIRES(env:XDOCTEST_TEST_DOITANYWAY)
                >>> print('hello')
            """
        ''')

    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_bad_preimport.py')
        with open(modpath, 'w') as file:
            file.write(source)
        os.environ['XDOCTEST_TEST_DOITANYWAY'] = ''
        with utils.CaptureStdout() as cap:
            runner.doctest_module(modpath, 'all', argv=[''])
        assert 'Failed to import modname' not in cap.text
        assert '1 skipped' in cap.text

        os.environ['XDOCTEST_TEST_DOITANYWAY'] = '1'
        with utils.CaptureStdout() as cap:
            runner.doctest_module(modpath, 'all', argv=[])
        assert 'Failed to import modname' in cap.text

        del os.environ['XDOCTEST_TEST_DOITANYWAY']

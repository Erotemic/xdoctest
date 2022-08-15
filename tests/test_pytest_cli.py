from xdoctest.utils import util_misc
import sys
from xdoctest import utils


def cmd(command):
    # simplified version of ub.cmd no fancy tee behavior
    import subprocess
    proc = subprocess.Popen(
        command, shell=True, universal_newlines=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = proc.communicate()
    ret = proc.wait()
    info = {
        'proc': proc,
        'out': out,
        'test_doctest_in_notebook.ipynberr': err,
        'ret': ret,
    }
    return info


def test_simple_pytest_cli():
    module_text = utils.codeblock(
        '''
        def module_func1():
            """
            This module has a doctest

            Example:
                >>> print('hello world')
            """
        ''')
    temp_module = util_misc.TempModule(module_text)
    modpath = temp_module.modpath

    info = cmd(sys.executable + ' -m pytest --xdoctest ' + modpath)
    print(info['out'])
    assert info['ret'] == 0


def test_simple_pytest_import_error_cli():
    """
    This test case triggers an excessively long callback in xdoctest <
    dev/0.15.7

    CommandLine:
        xdoctest ~/code/xdoctest/tests/test_pytest_cli.py test_simple_pytest_import_error_cli
    """
    module_text = utils.codeblock(
        '''
        # There are lines before the bad line
        import os
        import sys
        import does_not_exist

        def module_func1():
            """
            This module has a doctest

            Example:
                >>> print('hello world')
            """
        ''')
    temp_module = util_misc.TempModule(module_text, modname='imperr_test_mod')
    command = sys.executable + ' -m pytest -v -s --xdoctest-verbose=3 --xdoctest-supress-import-errors --xdoctest ' + temp_module.dpath
    print(command)
    print('--')
    info = cmd(command)
    print('--')
    # print('info = {}'.format(info))
    print(info['out'])
    # We patched doctest_example so it no longer outputs this in the traceback
    assert 'util_import' not in info['out']
    print(info['out'])
    # Note: flaky changes the return code from 1 to 3, so test non-zero
    assert info['ret'] != 0

    # Remove the supress import error flag and now we should get the traceback
    temp_module = util_misc.TempModule(module_text, modname='imperr_test_mod')
    command = sys.executable + ' -m pytest -v -s --xdoctest-verbose=3 --xdoctest ' + temp_module.dpath
    print(command)
    print('--')
    info = cmd(command)
    print('--')
    # print('info = {}'.format(info))
    print(info['out'])
    # We patched doctest_example so it no longer outputs this in the traceback
    assert 'util_import' in info['out']
    print(info['out'])
    # Note: flaky changes the return code from 1 to 3, so test non-zero
    assert info['ret'] != 0


def test_simple_pytest_syntax_error_cli():
    """
    """
    module_text = utils.codeblock(
        '''
        &&does_not_exist

        def module_func1():
            """
            This module has a doctest

            Example:
                >>> print('hello world')
            """
        ''')
    temp_module = util_misc.TempModule(module_text)
    info = cmd(sys.executable + ' -m pytest --xdoctest ' + temp_module.dpath)
    print(info['out'])
    assert info['ret'] != 0

    info = cmd(sys.executable + ' -m pytest --xdoctest ' + temp_module.modpath)
    print(info['out'])
    assert info['ret'] != 0


def test_simple_pytest_import_error_no_xdoctest():
    """
    """
    module_text = utils.codeblock(
        '''
        import does_not_exist

        def test_this():
            print('hello world')
        ''')
    temp_module = util_misc.TempModule(module_text)
    info = cmd(sys.executable + ' -m pytest ' + temp_module.modpath)
    print(info['out'])
    assert info['ret'] != 0

    info = cmd(sys.executable + ' -m pytest ' + temp_module.dpath)
    print(info['out'])
    assert info['ret'] != 0


def test_simple_pytest_syntax_error_no_xdoctest():
    """
    """
    module_text = utils.codeblock(
        '''
        &&does_not_exist

        def test_this():
            print('hello world')
        ''')
    temp_module = util_misc.TempModule(module_text)
    info = cmd(sys.executable + ' -m pytest ' + temp_module.modpath)
    print(info['out'])
    assert info['ret'] != 0

    info = cmd(sys.executable + ' -m pytest ' + temp_module.dpath)
    print(info['out'])
    assert info['ret'] != 0


def test_version_and_cli_info():
    """
    """
    import xdoctest
    info = cmd(sys.executable + ' -m xdoctest --version')
    assert info['out'].strip() == xdoctest.__version__

    info = cmd(sys.executable + ' -m xdoctest --version-info')
    assert xdoctest.__version__ in info['out']


def test_simple_xdoctest_cli():
    module_text = utils.codeblock(
        '''
        def module_func1():
            """
            This module has a doctest

            Example:
                >>> print('hello world')
            """
        ''')
    temp_module = util_misc.TempModule(module_text)
    modpath = temp_module.modpath
    info = cmd(sys.executable + ' -m xdoctest ' + modpath + ' --time')
    assert 'time:' in info['out']

    info = cmd(sys.executable + ' -m xdoctest ' + modpath + ' all')
    assert 'passed' in info['out']
    info = cmd(sys.executable + ' -m xdoctest ' + modpath + ' list')
    assert 'passed' not in info['out']
    info = cmd(sys.executable + ' -m xdoctest ' + modpath + ' --verbose=0')
    print(repr(info['out']))
    assert info['out'].strip() == ''


def test_simple_xdoctest_cli_errors():
    module_text = utils.codeblock(
        '''
        def module_func1():
            """
            This module has a doctest

            Example:
                >>> raise Exception
            """
        ''')
    temp_module = util_misc.TempModule(module_text)
    modpath = temp_module.modpath
    info = cmd(sys.executable + ' -m xdoctest ' + modpath + ' --time')
    assert '1 failed' in info['out']

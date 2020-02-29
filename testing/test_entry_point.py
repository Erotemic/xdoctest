import sys
import os
import subprocess
import pytest
from xdoctest import utils


def cmd(command):
    # simplified version of ub.cmd no fancy tee behavior
    proc = subprocess.Popen(
        command, shell=True, universal_newlines=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = proc.communicate()
    ret = proc.wait()
    info = {
        'proc': proc,
        'out': out,
        'err': err,
        'ret': ret,
    }
    return info


def skip_if_not_installed():
    # If xdoctest is not installed via `pip install -e`
    # then skip these tests because the entry point wont exist
    if not utils.is_modname_importable('xdoctest'):
        pytest.skip('Can only test entry points if xdoctest is installed.')


def test_xdoc_console_script_location():
    skip_if_not_installed()

    if sys.platform.startswith('win32'):
        pytest.skip()
        path = os.path.realpath(sys.executable)
        for i in range(4):
            path = os.path.dirname(path)
            print('path = {!r}'.format(path))
            scriptdir = os.path.join(path, 'Scripts')
            if os.path.exists(scriptdir):
                break
        script_path = os.path.join(scriptdir, 'xdoctest.exe')
        assert os.path.exists(script_path)
        # info = cmd('where xdoctest.exe')
        return
    else:
        info = cmd('which xdoctest')

    out = info['out']
    script_fpath = out.strip()
    script_fname = os.path.basename(script_fpath)
    assert script_fname.startswith('xdoctest')


def test_xdoc_console_script_exec():
    skip_if_not_installed()
    if sys.platform.startswith('win32'):
        path = os.path.realpath(sys.executable)
        for i in range(4):
            path = os.path.dirname(path)
            print('path = {!r}'.format(path))
            scriptdir = os.path.join(path, 'Scripts')
            if os.path.exists(scriptdir):
                break
        info = cmd(os.path.join(scriptdir, 'xdoctest.exe'))
    else:
        info = cmd('xdoctest')
    print('info = {!r}'.format(info))
    assert 'usage' in info['err']


def test_xdoc_cli_version():
    """
    CommandLine:
        python -m xdoctest -m ~/code/xdoctest/testing/test_entry_point.py test_xdoc_cli_version
    """
    import sys
    if sys.platform.startswith('win32'):
        pytest.skip()

    import xdoctest
    from xdoctest import __main__
    print('xdoctest = {!r}'.format(xdoctest))
    print('__main__ = {!r}'.format(__main__))
    retcode = __main__.main(argv=['--version'])
    print('retcode = {!r}'.format(retcode))
    assert retcode == 0

    import xdoctest
    print('xdoctest = {!r}'.format(xdoctest))

    sys.executable
    try:
        import ubelt as ub
    except ImportError:
        info = cmd(sys.executable + ' -m xdoctest --version')
    else:
        info = ub.cmd(sys.executable + ' -m xdoctest --version')
    print('info = {!r}'.format(info))
    print('xdoctest.__version__ = {!r}'.format(xdoctest.__version__))
    assert xdoctest.__version__ in info['out']


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdoctest/testing/test_entry_point.py
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

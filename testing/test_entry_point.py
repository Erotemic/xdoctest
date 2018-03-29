import sys
import os
import subprocess
import pytest
from xdoctest import static_analysis as static


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
    if not static.is_modname_importable('xdoctest'):
        pytest.skip('Can only test entry points if xdoctest is installed.')


def test_xdoc_console_script_location():
    skip_if_not_installed()

    if sys.platform.startswith('win32'):
        path = os.path.realpath(sys.argv[0])
        print('path = {!r}'.format(path))
        site_packages = os.path.dirname(path)
        print('site_packages = {!r}'.format(site_packages))
        print(os.listdir(site_packages))
        pythondir = os.path.dirname(os.path.dirname(site_packages))
        scriptdir = os.path.join(pythondir, 'Scripts')
        print('pythondir = {!r}'.format(pythondir))
        print('scriptdir = {!r}'.format(scriptdir))
        print(os.listdir(scriptdir))

        info = cmd('where xdoctest')
    else:
        info = cmd('which xdoctest')
    print('info = {!r}'.format(info))
    out = info['out']
    print('out = {!r}'.format(out))
    script_fpath = out.strip()
    print('script_fpath = {!r}'.format(script_fpath))
    script_fname = os.path.basename(script_fpath)
    print('script_fname = {!r}'.format(script_fname))
    assert script_fname.startswith('xdoctest')


def test_xdoc_console_script_exec():
    skip_if_not_installed()

    if sys.platform.startswith('win32'):
        path = os.path.realpath(sys.argv[0])
        print('path = {!r}'.format(path))
        site_packages = os.path.dirname(path)
        print('site_packages = {!r}'.format(site_packages))
        print(os.listdir(site_packages))
        pythondir = os.path.dirname(os.path.dirname(site_packages))
        scriptdir = os.path.join(pythondir, 'Scripts')
        print('pythondir = {!r}'.format(pythondir))
        print('scriptdir = {!r}'.format(scriptdir))
        print(os.listdir(scriptdir))

        info = cmd('xdoctest')
    else:
        info = cmd('xdoctest')
    print('info = {!r}'.format(info))
    assert 'usage' in info['err']

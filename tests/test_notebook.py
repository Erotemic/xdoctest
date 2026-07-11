from __future__ import annotations

import sys
from os.path import dirname, exists, join
from typing import Any

import pytest

try:
    from packaging.version import parse as LooseVersion
except ImportError:
    from distutils.version import LooseVersion  # type: ignore

PY_VERSION = LooseVersion('{}.{}'.format(*sys.version_info[0:2]))
IS_MODERN_PYTHON = PY_VERSION > LooseVersion('3.4')


def skip_notebook_tests_if_unsupported() -> None:
    if not IS_MODERN_PYTHON:
        pytest.skip('jupyter support is only for modern python versions')

    try:
        import IPython  # NOQA
        import nbconvert  # NOQA
        import nbformat  # NOQA
        import jupyter_client.kernelspec

        kernel_name = jupyter_client.kernelspec.NATIVE_KERNEL_NAME
        try:
            jupyter_client.kernelspec.get_kernel_spec(kernel_name)
        except jupyter_client.kernelspec.NoSuchKernel:
            pytest.skip('No Jupyter kernel named {!r}'.format(kernel_name))

        import platform

        if platform.python_implementation() == 'PyPy':
            # In xdoctest <= 0.15.0 (~ 2021-01-01) this didn't cause an issue
            # But I think there was a jupyter update that broke it.
            # PyPy + Jupyter is currently very niche and I don't have the time
            # to debug properly, so I'm just turning off these tests.
            raise Exception

    except Exception:
        pytest.skip('Missing jupyter')


def cmd(command: str) -> dict[str, 'Any']:
    # simplified version of ub.cmd no fancy tee behavior
    import subprocess

    proc = subprocess.Popen(
        command,
        shell=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = proc.communicate()
    ret = proc.wait()
    info: dict[str, 'Any'] = {
        'proc': proc,
        'out': out,
        'test_doctest_in_notebook.ipynberr': err,
        'ret': ret,
    }
    return info


def demodata_notebook_fpath() -> str:
    try:
        testdir = dirname(__file__)
    except NameError:
        # Hack for dev CLI usage
        import os

        testdir = os.path.expandvars('$HOME/code/xdoctest/tests/')
        assert exists(testdir), 'assuming a specific dev environment'
    notebook_fpath = join(testdir, 'notebook_with_doctests.ipynb')
    return notebook_fpath


def test_xdoctest_inside_notebook() -> None:
    """
    xdoctest ~/code/xdoctest/tests/test_notebook.py test_xdoctest_inside_notebook
    xdoctest tests/test_notebook.py test_xdoctest_inside_notebook

    xdoctest notebook_with_doctests.ipynb
    """
    # How to run Jupyter from Python
    # https://nbconvert.readthedocs.io/en/latest/execute_api.html
    skip_notebook_tests_if_unsupported()

    notebook_fpath = demodata_notebook_fpath()

    from xdoctest.utils import util_notebook

    nb, resources = util_notebook.execute_notebook(notebook_fpath, verbose=3)

    last_cell = nb['cells'][-1]
    text = last_cell['outputs'][0]['text']
    if '3 / 3 passed' not in text:
        import warnings

        warnings.warn(
            'test_xdoctest_inside_notebook might fail due to io issues'
        )


def test_xdoctest_outside_notebook() -> None:
    skip_notebook_tests_if_unsupported()

    if sys.platform.startswith('win32'):
        pytest.skip()

    notebook_fpath = demodata_notebook_fpath()
    info = cmd(sys.executable + ' -m xdoctest ' + notebook_fpath)
    text = info['out']
    assert isinstance(text, str)
    assert '3 / 3 passed' in text


def test_missing_kernel_is_treated_as_unsupported(monkeypatch) -> None:
    jupyter_client = pytest.importorskip('jupyter_client')
    pytest.importorskip('IPython')
    pytest.importorskip('nbconvert')
    pytest.importorskip('nbformat')

    def _raise_no_such_kernel(kernel_name):
        raise jupyter_client.kernelspec.NoSuchKernel(kernel_name)

    monkeypatch.setattr(
        jupyter_client.kernelspec,
        'get_kernel_spec',
        _raise_no_such_kernel,
    )
    with pytest.raises(pytest.skip.Exception, match='No Jupyter kernel'):
        skip_notebook_tests_if_unsupported()


def test_make_notebook_without_registered_kernel(monkeypatch, tmp_path) -> None:
    jupyter_client = pytest.importorskip('jupyter_client')
    nbformat = pytest.importorskip('nbformat')
    from xdoctest.utils import util_notebook

    def _raise_no_such_kernel(kernel_name):
        raise jupyter_client.kernelspec.NoSuchKernel(kernel_name)

    monkeypatch.setattr(
        jupyter_client.kernelspec,
        'get_kernel_spec',
        _raise_no_such_kernel,
    )
    fpath = tmp_path / 'demo.ipynb'
    util_notebook._make_test_notebook_fpath(fpath, ['x = 1'])
    with fpath.open('r') as file:
        notebook = nbformat.read(file, as_version=nbformat.NO_CONVERT)
    assert notebook.metadata.kernelspec.name == 'python3'
    assert notebook.metadata.kernelspec.display_name == 'Python 3'
    assert notebook.metadata.kernelspec.language == 'python'

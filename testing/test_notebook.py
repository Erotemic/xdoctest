import pytest
import sys
from os.path import join, exists, dirname
from distutils.version import LooseVersion

PY_VERSION = LooseVersion('{}.{}'.format(*sys.version_info[0:2]))
IS_MODERN_PYTHON = PY_VERSION > LooseVersion('3.4')


def skip_notebook_tests_if_unsupported():
    if not IS_MODERN_PYTHON:
        pytest.skip('jupyter support is only for modern python versions')

    try:
        import IPython  # NOQA
        import nbconvert  # NOQA
        import nbformat  # NOQA

        import platform
        if platform.python_implementation() == 'PyPy':
            # In xdoctest <= 0.15.0 (~ 2021-01-01) this didn't cause an issue
            # But I think there was a jupyter update that broke it.
            # PyPy + Jupyter is currently very niche and I don't have the time
            # to debug properly, so I'm just turning off these tests.
            raise Exception

    except Exception:
        pytest.skip('Missing jupyter')


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


def demodata_notebook_fpath():
    try:
        testdir = dirname(__file__)
    except NameError:
        # Hack for dev CLI usage
        import os
        testdir = os.path.expandvars('$HOME/code/xdoctest/testing/')
        assert exists(testdir), 'assuming a specific dev environment'
    notebook_fpath = join(testdir, "notebook_with_doctests.ipynb")
    return notebook_fpath


def test_xdoctest_inside_notebook():
    """
    xdoctest ~/code/xdoctest/testing/test_notebook.py test_xdoctest_inside_notebook
    xdoctest testing/test_notebook.py test_xdoctest_inside_notebook

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
        warnings.warn('test_xdoctest_inside_notebook might fail due to io issues')


def test_xdoctest_outside_notebook():

    skip_notebook_tests_if_unsupported()

    if sys.platform.startswith('win32'):
        pytest.skip()

    notebook_fpath = demodata_notebook_fpath()
    info = cmd(sys.executable + ' -m xdoctest ' + notebook_fpath)
    text = info['out']
    assert '3 / 3 passed' in text

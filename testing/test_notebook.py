import six
import pytest
from os.path import join, exists


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

    xdoctest notebook_with_doctests.ipynb
    """
    # How to run Jupyter from Python
    # https://nbconvert.readthedocs.io/en/latest/execute_api.html
    if six.PY2:
        pytest.skip('cannot test this case in Python2')

    notebook_fpath = demodata_notebook_fpath()

    from xdoctest.utils import util_notebook
    nb, resources = util_notebook.execute_notebook(notebook_fpath)

    last_cell = nb['cells'][-1]
    text = last_cell['outputs'][0]['text']
    assert '3 / 3 passed' in text


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
        'err': err,
        'ret': ret,
    }
    return info


def test_xdoctest_outside_notebook():
    import sys
    import pytest
    if sys.platform.startswith('win32'):
        pytest.skip()
    notebook_fpath = demodata_notebook_fpath()
    info = cmd(sys.executable + ' -m xdoctest ' + notebook_fpath)
    text = info['out']
    assert '3 / 3 passed' in text

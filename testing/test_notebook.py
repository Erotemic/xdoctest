def test_notebook():
    """
    xdoctest ~/code/xdoctest/testing/test_notebook.py test_notebook

    xdoctest notebook_with_doctests.ipynb
    """
    # How to run Jupyter from Python
    # https://nbconvert.readthedocs.io/en/latest/execute_api.html
    import six
    import pytest
    if six.PY2:
        pytest.skip('cannot test this case in Python2')

    import nbformat
    from nbconvert.preprocessors import ExecutePreprocessor
    from os.path import dirname, join, exists

    try:
        testdir = dirname(__file__)
    except NameError:
        # Hack for dev CLI usage
        import os
        testdir = os.path.expandvars('$HOME/code/xdoctest/testing/')
        assert exists(testdir), 'assuming a specific dev environment'

    notebook_fpath = join(testdir, "notebook_with_doctests.ipynb")
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    with open(notebook_fpath) as file:
        nb = nbformat.read(file, as_version=nbformat.NO_CONVERT)
    ep.preprocess(nb, {'metadata': {'path': testdir}})

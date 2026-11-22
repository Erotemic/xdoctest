Installing Python
=================

Xdoctest 1.4.0 requires Python 3.10 or newer. Install Python from
`python.org <https://www.python.org/downloads/>`_ or create an isolated
`conda <https://docs.conda.io/en/latest/>`_ environment.

For example, after installing Miniconda following the
`official instructions <https://docs.conda.io/projects/miniconda/en/latest/>`_,
create and activate a compatible environment:

.. code-block:: bash

    conda create --name xdoctest python=3.10 --yes
    conda activate xdoctest
    python -m pip install xdoctest

You can choose any newer supported Python version instead of 3.10.
For working with virtual environments without conda, see the
`Python venv documentation <https://docs.python.org/3/library/venv.html>`_.

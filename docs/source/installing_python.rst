Installing Python 
=================

Before you can use xdoctest, you must have Python installed. Its also best
practice to be in a `virtual environment <https://realpython.com/effective-python-environment/>`_.
If you are a Python beginner, then I would recommend setting up a 
`conda <https://docs.conda.io/en/latest/>`_ environment. 
I typically do this on Linux as follows:

.. code:: bash

    # Download the conda install script
    mkdir -p ~/tmp
    cd ~/tmp
    CONDA_INSTALL_SCRIPT=Miniconda3-latest-Linux-x86_64.sh
    curl https://repo.anaconda.com/miniconda/$CONDA_INSTALL_SCRIPT > $CONDA_INSTALL_SCRIPT
    chmod +x $CONDA_INSTALL_SCRIPT

    # Install miniconda to user local directory
    _CONDA_ROOT=$HOME/.local/conda
    sh $CONDA_INSTALL_SCRIPT -b -p $_CONDA_ROOT
    # Activate the basic conda environment
    source $_CONDA_ROOT/etc/profile.d/conda.sh
    # Update the base and create the virtual environment
    conda update -y -n base conda
    conda create -y -n py38 python=3.8

    # Activate your vitualenv
    # I recommend adding the following steps to your ~/.bashrc
    _CONDA_ROOT=$HOME/.local/conda
    source $_CONDA_ROOT/etc/profile.d/conda.sh
    conda activate py38

Once you have created this conda environment, I recommend adding the following
lines to your ``.bashrc``.


.. code:: bash

    # Enables the conda command
    _CONDA_ROOT=$HOME/.local/conda
    source $_CONDA_ROOT/etc/profile.d/conda.sh

    if [ -d "$HOME/.local/conda/envs/py38" ]; then
        # Always start in a virtual environment
        conda activate py38
    fi

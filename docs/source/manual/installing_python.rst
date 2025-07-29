Installing Python
=================

Before you can use xdoctest, you must have Python installed. Its also best
practice to be in a `virtual environment <https://realpython.com/effective-python-environment/>`_.
If you are a Python beginner, then I would recommend setting up a
`conda <https://docs.conda.io/en/latest/>`_ environment.


On Linux, I typically use this end-to-end script for installing conda,
creating, and activating a virtual environment.

.. code-block:: bash

    # Download the conda install script into a temporary directory
    mkdir -p ~/tmp
    cd ~/tmp

    # To update to a newer version see:
    # https://docs.conda.io/en/latest/miniconda_hashes.html for updating
    CONDA_INSTALL_SCRIPT=Miniconda3-py38_4.9.2-Linux-x86_64.sh
    CONDA_EXPECTED_SHA256=1314b90489f154602fd794accfc90446111514a5a72fe1f71ab83e07de9504a7
    curl https://repo.anaconda.com/miniconda/$CONDA_INSTALL_SCRIPT > $CONDA_INSTALL_SCRIPT
    CONDA_GOT_SHA256=$(sha256sum $CONDA_INSTALL_SCRIPT | cut -d' ' -f1)
    # For security, it is important to verify the hash
    if [[ "$CONDA_GOT_SHA256" != "$CONDA_EXPECTED_SHA256_HASH" ]]; then
        echo "Downloaded file does not match hash! DO NOT CONTINUE!"
        exit 1;
    fi
    chmod +x $CONDA_INSTALL_SCRIPT

    # Install miniconda to user local directory
    _CONDA_ROOT=$HOME/.local/conda
    sh $CONDA_INSTALL_SCRIPT -b -p $_CONDA_ROOT
    # Activate the basic conda environment
    source $_CONDA_ROOT/etc/profile.d/conda.sh
    # Update the base and create a virtual environment named py38
    conda update --name base conda --yes
    conda create --name py38 python=3.8 --yes

    # Activate your virtualenv
    # I recommend doing something similar in your ~/.bashrc
    source $_CONDA_ROOT/etc/profile.d/conda.sh
    conda activate py38

Once you have created this conda environment, I recommend adding the following
lines to your ``.bashrc``. This way you will automatically activate your
virtual environment whenever you start a new bash shell.

.. code-block:: bash

    # Enables the conda command
    _CONDA_ROOT=$HOME/.local/conda
    source $_CONDA_ROOT/etc/profile.d/conda.sh

    if [ -d "$HOME/.local/conda/envs/py38" ]; then
        # Always start in a virtual environment
        conda activate py38
    fi


For other operating systems, see the official documentation to install conda
`on Windows <https://docs.conda.io/projects/conda/en/latest/user-guide/install/windows.html>`_ or
`on MacOS <https://docs.conda.io/projects/conda/en/latest/user-guide/install/macos.html>`_.

Once conda is installed the commands for `managing conda virtual environments <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#>`_ are roughly the same across platforms.

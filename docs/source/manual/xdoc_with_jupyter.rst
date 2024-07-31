Running Doctests in Jupyter Notebooks
-------------------------------------

You can run doctests within a Jupyter notebook in two ways:

Method 1 - Inside the notebook
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Either insert this cell into your notebook:

.. code:: python

   if __name__ == '__main__':
       import xdoctest
       xdoctest.doctest_module()

This will execute any doctests for callables that are in the top-level
namespace of the notebook. While you don’t have to include the
``if __name__`` block, it is better practice because it will prevent
issues if you also wish to use “Method 2”.

Method 2 - Outside the notebook
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An alternative way to run would be using the xdoctest command line tool
and pointing to the notebook file.

.. code:: bash

   xdoctest path/to/notebook.ipynb

This will execute *every* cell in the notebook and then execute the
doctest of any defined callable with a doctest.

Caveats
~~~~~~~

WARNING: in both of the above methods, when you execute doctests it will
include any function / class that was defined in the notebook, but also
*any external library callable with a doctest that you import directly*!
Therefore it is best to (1) never use ``from <module> import *``
statements (in general using ``import *`` is bad practice) and (2)
prefer using functions via their module name rather than importing
directory. For example instead of
``from numpy import array; x = array([1])`` use
``import numpy as np; x = np.array([1])``.

Lastly, it is important to note that Jupyter notebooks are great for
prototyping and exploration, but in practice storing algorithm and
utilities in Jupyter notebooks is not sustainable (`for some of these
reasons`_). Reusable code should eventually be refactored into a `proper
pip-installable Python package`_ where the top level directory contains
a ``setup.py`` and a folder with a name corresponding to the module name
and containing an ``__init__.py`` file and any other package python
files. However, if you write you original Jupyter code with doctests,
then when you port your code to a proper package the automated tests
come with it! (And the above warning does *not* apply to statically
parsed python packages)

.. _for some of these reasons: https://github.com/grst/nbimporter#update-2019-06-i-do-not-recommend-any-more-to-use-nbimporter
.. _proper pip-installable Python package: https://packaging.python.org/tutorials/packaging-projects/

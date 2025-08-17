# :github_url: https://github.com/Erotemic/xdoctest
'''

.. The large version wont work because github strips rst image rescaling. https://i.imgur.com/u0tYYxM.png
.. image:: https://i.imgur.com/u0tYYxM.png
   :height: 100px
   :align: left


.. note that the following few characters are invisible unicode characters so
.. we can hack the position of the title

⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀

Xdoctest - Execute Doctests
===========================

Xdoctest is a Python package for executing tests in documentation strings!

What is a `doctest <https://en.wikipedia.org/wiki/Doctest>`__?
It is example code you write in a docstring!
What is a `docstring <https://en.wikipedia.org/wiki/Docstring>`__?
Its a string you use as a comment! They get attached to Python functions and
classes as metadata. They are often used to auto-generate documentation.
Why is it cool?
Because you can write tests while you code!


Xdoctest finds and executes your doctests for you.
Just run ``xdoctest <path-to-my-module>``.
It plugs into pytest to make it easy to run on a CI. Install and run
``pytest --xdoctest``.


The :py:mod:`xdoctest` package is a re-write of Python's builtin
:py:mod:`doctest` module. It replaces the old regex-based parser with a new
abstract-syntax-tree based parser (using Python's :py:mod:`ast` module). The
goal is to make doctests easier to write, simpler to configure, and encourage
the pattern of test driven development.


+---------------+-------------------------------------------+
| Read the docs | http://xdoctest.readthedocs.io/en/latest  |
+---------------+-------------------------------------------+
| Github        | https://github.com/Erotemic/xdoctest      |
+---------------+-------------------------------------------+
| Pypi          | https://pypi.org/project/xdoctest         |
+---------------+-------------------------------------------+
| PyCon 2020    | `Youtube Video`_ and `Google Slides`_     |
+---------------+-------------------------------------------+

.. _Youtube Video: https://www.youtube.com/watch?v=CUjCqOw_oFk
.. _Google Slides: https://docs.google.com/presentation/d/1563XL-n7534QmktrkLSjVqX36z5uhjUFrPw8wIO6z1c


Getting Started 0:  Installation
--------------------------------

First ensure that you have
:doc:`Python installed <../manual/installing_python>` and ideally are in a
virtual environment. Install xdoctest using the pip.

.. code:: bash

    pip install xdoctest

Alternatively you can install xdoctest with optional packages.

.. code:: bash

    pip install xdoctest[all]

This ensures that the :py:mod:`pygments` and :py:mod:`colorama` packages are
installed, which are required to color terminal output.


Getting Started 1: Your first doctest
-------------------------------------

If you already know how to write a doctest then you can skip to the next
section. If you aren't familiar with doctests, this will help get you up to
speed.

Consider the following implementation the Fibonacci function.

.. code:: python

    def fib(n):
         """
         Python 3: Fibonacci series up to n
         """
         a, b = 0, 1
         while a < n:
             print(a, end=' ')
             a, b = b, a+b
         print()

We can add a "doctest" in the "docstring" as both an example and a test of the
code. All we have to do is prefix the doctest code with three right chevrons
`` >>> ``. We can also use xdoctest directives to control the flow of doctest
execution.

.. code:: python

    def fib(n):
        """
        Python 3: Fibonacci series up to n

        Example:
            >>> fib(1000) # xdoctest: +SKIP
            0 1 1 2 3 5 8 13 21 34 55 89 144 233 377 610 987
        """
        a, b = 0, 1
        while a < n:
            print(a, end=' ')
            a, b = b, a+b
        print()

Now if this text was in a file called ``fib.py`` you could execute your doctest
by running ``xdoctest fib.py``. Note that if ``fib.py`` was in a package called
``mymod``, you could equivalently run ``xdoctest -m mymod.fib``. In other words
you can all doctests in a file by passing xdoctest the module name or the
module path.


Interestingly because this documentation is written in the
``xdoctest/__init__.py`` file, which is a Python file, that means we can write
doctests in it.  If you have xdoctest installed, you can use the xdoctest cli
to execute the following code:  ``xdoctest -m xdoctest.__init__ __doc__:0``.
Also notice that the previous doctest is skipped due to the SKIP directive.
For more information on directives see
:doc:`the docs for the xdoctest directive module<auto/xdoctest.directive>`.


.. code:: python

    >>> # Python 3: Fibonacci series up to n
    >>> def fib(n):
    >>>     a, b = 0, 1
    >>>     while a < n:
    >>>         print(a, end=' ')
    >>>         a, b = b, a+b
    >>>     print()
    >>> fib(25)
    0 1 1 2 3 5 8 13 21


Getting Started 2: Running your doctests
----------------------------------------


There are two ways to run xdoctest: (1) :py:mod:`pytest` or (2) the native
:py:mod:`xdoctest` interface. The native interface is less opaque and implicit,
but its purpose is to run doctests. The other option is to use the widely used
pytest package.  This allows you to run both unit tests and doctests with the
same command and has many other advantages.

It is recommended to use pytest for automatic testing (e.g. in your CI
scripts), but for debugging it may be easier to use the native interface.

Using the pytest interface
^^^^^^^^^^^^^^^^^^^^^^^^^^

When pytest is run, xdoctest is automatically discovered, but is disabled by
default. This is because xdoctest needs to replace the builtin
:py:mod:`pytest._pytest.doctest` plugin.

To enable this plugin, run ``pytest`` with ``--xdoctest`` or ``--xdoc``.
This can either be specified on the command line or added to your
``addopts`` options in the ``[pytest]`` section of your ``pytest.ini``
or ``tox.ini``.

To run a specific doctest, xdoctest sets up pytest node names
for these doctests using the following pattern:
``<path/to/file.py>::<callname>:<num>``. For example a doctest for a
function might look like this ``mymod.py::funcname:0``, and a class
method might look like this: ``mymod.py::ClassName::method:0``

Using the native interface.
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :py:mod:`xdoctest` module contains a :py:mod:`pytest` plugin, but also
contains a native command line interface (CLI). The CLI is generated using
:py:mod:`argparse`.

For help you can run

.. code-block:: bash

    xdoctest --help


which produces something similar to the following output:

.. code-block:: text

    usage: xdoctest [-h] [--version] [-m MODNAME] [-c COMMAND] [--style {auto,google,freeform}] [--analysis {auto,static,dynamic}] [--durations DURATIONS] [--time]
                    [--colored COLORED] [--nocolor] [--offset] [--report {none,cdiff,ndiff,udiff,only_first_failure}] [--options OPTIONS] [--global-exec GLOBAL_EXEC]
                    [--verbose VERBOSE] [--quiet] [--silent]
                    [arg ...]

    Xdoctest 1.0.0 - on Python - 3.9.9 (main, Jan  6 2022, 18:33:12)
    [GCC 10.3.0] - discover and run doctests within a python package

    positional arguments:
      arg                   Ignored if optional arguments are specified, otherwise: Defaults --modname to arg.pop(0). Defaults --command to arg.pop(0). (default: None)

    optional arguments:
      -h, --help            show this help message and exit
      --version             Display version info and quit (default: False)
      -m MODNAME, --modname MODNAME
                            Module name or path. If specified positional modules are ignored (default: None)
      -c COMMAND, --command COMMAND
                            A doctest name or a command (list|all|<callname>). Defaults to all (default: None)
      --style {auto,google,freeform}
                            Choose the style of doctests that will be parsed (default: auto)
      --analysis {auto,static,dynamic}
                            How doctests are collected (default: auto)
      --durations DURATIONS
                            Specify execution times for slowest N tests.N=0 will show times for all tests (default: None)
      --time                Same as if durations=0 (default: False)
      --colored COLORED     Enable or disable ANSI coloration in stdout (default: True)
      --nocolor             Disable ANSI coloration in stdout
      --offset              If True formatted source linenumbers will agree with their location in the source file. Otherwise they will be relative to the doctest itself. (default:
                            False)
      --report {none,cdiff,ndiff,udiff,only_first_failure}
                            Choose another output format for diffs on xdoctest failure (default: udiff)
      --options OPTIONS     Default directive flags for doctests (default: None)
      --global-exec GLOBAL_EXEC
                            Custom Python code to execute before every test (default: None)
      --verbose VERBOSE     Verbosity level. 0 is silent, 1 prints out test names, 2 additionally prints test stdout, 3 additionally prints test source (default: 3)
      --quiet               sets verbosity to 1
      --silent              sets verbosity to 0



The xdoctest interface can be run programmatically using
``xdoctest.doctest_module(path)``, which can be placed in the ``__main__``
section of any module as such:

.. code-block:: python

    if __name__ == '__main__':
        import xdoctest
        xdoctest.doctest_module(__file__)

This sets up the ability to invoke the ``xdoctest`` command line interface by
invoking your module as a
`main script <https://docs.python.org/3/using/cmdline.html#cmdoption-m>`_:
``python -m <modname> <command>``, where ``<modname>`` is the name of your
module (e.g. `foo.bar`) and command follows the following rules:


-  If ``<command>`` is ``all``, then each enabled doctest in the module
   is executed: ``python -m <modname> all``

-  If ``<command>`` is ``list``, then the names of each enabled doctest
   is listed.

-  If ``<command>`` is ``dump``, then all doctests are converted into a format
   suitable for unit testing, and dumped to stdout (new in 0.4.0).

-  If ``<command>`` is a "callname" (name of a function or a class and
   method), then that specific doctest is executed:
   ``python -m <modname> <callname>``. Note: you can execute disabled
   doctests or functions without any arguments (zero-args) this way.


XDoctest is a good demonstration of itself. After pip installing xdoctest, try
running xdoctest on xdoctest.

.. code:: bash

    xdoctest xdoctest

If you would like a slightly less verbose output, try

.. code:: bash

    xdoctest xdoctest --verbose=1

    # or

    xdoctest xdoctest --verbose=0


You could also consider running xdoctests tests through pytest:


.. code:: bash

    pytest $(python -c 'import xdoctest, pathlib; print(pathlib.Path(xdoctest.__file__).parent)') --xdoctest


If you would like a slightly more verbose output, try

.. code:: bash

    pytest -s --verbose --xdoctest-verbose=3 --xdoctest $(python -c 'import xdoctest, pathlib; print(pathlib.Path(xdoctest.__file__).parent)')


If you ran these commands, the myriad of characters that flew across your
screen are lots more examples of what you can do with doctests.


You can also run doctests
:doc:`inside Jupyter Notebooks <../manual/xdoc_with_jupyter>`.
'''


__autogen__ = '''
mkinit xdoctest --nomods
'''

__version__ = '1.3.0'


# Expose only select submodules
__submodules__ = [
    'runner',
    'exceptions',
]


from xdoctest import utils
from xdoctest import docstr
from xdoctest.runner import (doctest_module, doctest_callable,)
from xdoctest.exceptions import (DoctestParseError, ExitTestException,
                                 MalformedDocstr, ExistingEventLoopError)

__all__ = ['DoctestParseError', 'ExitTestException', 'MalformedDocstr',
           'ExistingEventLoopError',
           'doctest_module', 'doctest_callable', 'utils', 'docstr',
           '__version__']

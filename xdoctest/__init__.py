# -*- coding: utf-8 -*-
'''

XDoctest - Extended Doctest
===========================

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

First ensure that you have :doc:`Python installed <../installing_python>` and
ideally are in a virtual environment. Install xdoctest using the pip.

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
Also notice that the previous code prefixed with ``>>> `` is skipped due to the
xdoctest ``SKIP`` :doc:`directive<xdoctest.directive>`. For more information on
directives see :doc:`the docs for the xdoctest directive
module<xdoctest.directive>`.


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

    usage: xdoctest [-h] [--version] [-m MODNAME] [-c COMMAND] [--style {auto,google,freeform}] [--analysis {auto,static,dynamic}]
                    [--durations DURATIONS] [--time] [--colored COLORED] [--nocolor] [--offset]
                    [--report {none,cdiff,ndiff,udiff,only_first_failure}] [--options OPTIONS] [--global-exec GLOBAL_EXEC]
                    [--verbose VERBOSE] [--quiet] [--silent]
                    [arg [arg ...]]

    Xdoctest 0.15.0 - on Python - 3.8.3 (default, Jul  2 2020, 16:21:59)
    [GCC 7.3.0] - discover and run doctests within a python package

    positional arguments:
      arg                   Ignored if optional arguments are specified, otherwise: Defaults --modname to arg.pop(0). Defaults --command
                            to arg.pop(0). (default: None)

    optional arguments:
      -h, --help            show this help message and exit
      --version             display version info and quit (default: False)
      -m MODNAME, --modname MODNAME
                            module name or path. If specified positional modules are ignored (default: None)
      -c COMMAND, --command COMMAND
                            a doctest name or a command (list|all|<callname>). Defaults to all (default: None)
      --style {auto,google,freeform}
                            choose the style of doctests that will be parsed (default: auto)
      --analysis {auto,static,dynamic}
                            How doctests are collected (default: static)
      --durations DURATIONS
                            specify execution times for slowest N tests.N=0 will show times for all tests (default: None)
      --time                Same as if durations=0 (default: False)
      --colored COLORED     Enable or disable ANSI coloration in stdout (default: True)
      --nocolor             Disable ANSI coloration in stdout
      --offset              if True formatted source linenumbers will agree with their location in the source file. Otherwise they will
                            be relative to the doctest itself. (default: False)
      --report {none,cdiff,ndiff,udiff,only_first_failure}
                            choose another output format for diffs on xdoctest failure (default: udiff)
      --options OPTIONS     default directive flags for doctests (default: None)
      --global-exec GLOBAL_EXEC
                            exec these lines before every test (default: None)
      --verbose VERBOSE     verbosity level (default: 3)
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


You can also run doctests
:doc:`inside Jupyter Notebooks <../xdoc_with_jupyter>`.
'''


__autogen__ = '''
mkinit xdoctest --nomods
'''

__version__ = '0.15.2'


# Expose only select submodules
__submodules__ = [
    'runner',
    'exceptions',
]


from xdoctest import utils
from xdoctest import docstr
from xdoctest.runner import (doctest_module, doctest_callable,)
from xdoctest.exceptions import (DoctestParseError, ExitTestException,
                                 MalformedDocstr,)


def _parse_changelog(fpath):
    """
    Helper to parse the changelog for the version to verify versions agree.

    CommandLine:
        xdoctest ~/code/xdoctest/xdoctest/__init__.py _parse_changelog --dev

    Example:
        >>> # xdoctest: +REQUIRES(--dev)
        >>> fpath = 'CHANGELOG.md'
        >>> _parse_changelog(fpath)
    """
    from distutils.version import LooseVersion
    import re
    pat = re.compile(r'#.*Version ([0-9]+\.[0-9]+\.[0-9]+)')
    # We can statically modify this to a constant value when we deploy
    versions = []
    with open(fpath, 'r') as file:
        for line in file.readlines():
            line = line.rstrip()
            if line:
                parsed = pat.search(line)
                if parsed:
                    print('parsed = {!r}'.format(parsed))
                    try:
                        version_text = parsed.groups()[0]
                        version = LooseVersion(version_text)
                        versions.append(version)
                    except Exception:
                        print('Failed to parse = {!r}'.format(line))

    import pprint
    print('versions = {}'.format(pprint.pformat(versions)))
    assert sorted(versions)[::-1] == versions

    import xdoctest
    changelog_version = versions[0]
    module_version = LooseVersion(xdoctest.__version__)
    print('changelog_version = {!r}'.format(changelog_version))
    print('module_version = {!r}'.format(module_version))
    assert changelog_version == module_version

__all__ = ['DoctestParseError', 'ExitTestException', 'MalformedDocstr',
           'doctest_module', 'doctest_callable', 'utils', 'docstr',
           '__version__']

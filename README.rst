|CircleCI| |Travis| |Appveyor| |Codecov| |Pypi| |Downloads| |ReadTheDocs|


.. The large version wont work because github strips rst image rescaling. 
.. image:: https://i.imgur.com/u0tYYxM.png
   :height: 100px
   :align: left

The ``xdoctest`` package is a re-write of Python's builtin ``doctest``
module. It replaces the old regex-based parser with a new
abstract-syntax-tree based parser (using Python's ``ast`` module). The
goal is to make doctests easier to write, simpler to configure, and
encourage the pattern of test driven development.


+------------------+----------------------------------------------+
| Read the docs    | https://xdoctest.readthedocs.io              |
+------------------+----------------------------------------------+
| Github           | https://github.com/Erotemic/xdoctest         |
+------------------+----------------------------------------------+
| Pypi             | https://pypi.org/project/xdoctest            |
+------------------+----------------------------------------------+
| PyCon 2020       | `Youtube Video`_ and `Google Slides`_        |
+------------------+----------------------------------------------+

.. _Youtube Video: https://www.youtube.com/watch?v=CUjCqOw_oFk
.. _Google Slides: https://docs.google.com/presentation/d/1563XL-n7534QmktrkLSjVqX36z5uhjUFrPw8wIO6z1c


Quick Start
-----------

Installation: from pypi
^^^^^^^^^^^^^^^^^^^^^^^

Xdoctest is distributed on pypi as a universal wheel and can be pip installed on
Python 2.7, Python 3.4+. Installations are tested on CPython and PyPy
implementations. 

::

    pip install xdoctest


Distributions on pypi are signed with a GPG public key: ``D297D757``. If you
care enough to check the gpg signature (hopefully pip will just do this in the
future), you should also verify this agrees with the contents of
``dev/public_gpg_key``. 


Usage: Run your Doctests
^^^^^^^^^^^^^^^^^^^^^^^^


After installing, the fastest way to run all doctests in your project
is:

::

    python -m xdoctest /path/to/your/pkg-or-module.py

or if your module has been pip-installed / is in the PYTHONPATH run

::

    python -m xdoctest yourmodname

Getting Started
---------------

There are two ways to use ``xdoctest``: via ``pytest`` or via the native
interface. The native interface is less opaque and implicit, but its
purpose is to run doctests. The other option is to use the widely used
``pytest`` package. This allows you to run both unit tests and doctests
with the same command and has many other advantages.

It is recommended to use ``pytest`` for automatic testing (e.g. in your
CI scripts), but for debugging it may be easier to use the native
interface.

Check if xdoctest will work on your package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can quickly check if ``xdoctest`` will work on your package
out-of-the box by installing it via pip and running
``python -m xdoctest <pkg> all``, where ``<pkg>`` is the path to your
python package / module (or its name if it is installed in your
``PYTHONPATH``).

For example with you might test if ``xdoctest`` works on ``networkx`` or
``sklearn`` as such: ``python -m xdoctest networkx all`` /
``python -m xdoctest sklearn all``.

Using the pytest interface
^^^^^^^^^^^^^^^^^^^^^^^^^^

When ``pytest`` is run, ``xdoctest`` is automatically discovered, but is
disabled by default. This is because ``xdoctest`` needs to replace the builtin
``doctest`` plugin.

To enable this plugin, run ``pytest`` with ``--xdoctest`` or ``--xdoc``.
This can either be specified on the command line or added to your
``addopts`` options in the ``[pytest]`` section of your ``pytest.ini``
or ``tox.ini``.

To run a specific doctest, ``xdoctest`` sets up ``pytest`` node names
for these doctests using the following pattern:
``<path/to/file.py>::<callname>:<num>``. For example a doctest for a
function might look like this ``mymod.py::funcname:0``, and a class
method might look like this: ``mymod.py::ClassName::method:0``

Using the native interface.
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``xdoctest`` module contains a ``pytest`` plugin, but also contains
a native interface. This interface is run programmatically using
``xdoctest.doctest_module(path)``, which can be placed in the
``__main__`` section of any module as such:

.. code:: python

    if __name__ == '__main__':
        import xdoctest as xdoc
        xdoc.doctest_module(__file__)

This sets up the ability to invoke the ``xdoctest`` command line
interface. ``python -m <modname> <command>``

-  If ``<command>`` is ``all``, then each enabled doctest in the module
   is executed: ``python -m <modname> all``

-  If ``<command>`` is ``list``, then the names of each enabled doctest
   is listed.

-  If ``<command>`` is ``dump``, then all doctests are converted into a format
   suitable for unit testing, and dumped to stdout (new in 0.4.0).

-  If ``<command>`` is a ``callname`` (name of a function or a class and
   method), then that specific doctest is executed:
   ``python -m <modname> <callname>``. Note: you can execute disabled
   doctests or functions without any arguments (zero-args) this way.

For example if you created a module ``mymod.py`` with the following
code:

.. code:: python


    def func1():
        """
        Example:
            >>> assert func1() == 1
        """
        return 1

    def func2(a):
        """
        Example:
            >>> assert func2(1) == 2
            >>> assert func2(2) == 3
        """
        return a + 1

    if __name__ == '__main__':
        import xdoctest as xdoc
        xdoc.doctest_module(__file__)

You could 

* Use the command ``python -m mymod list`` to list the names of all functions with doctests
* Use the command ``python -m mymod all`` to run all functions with doctests
* Use the command ``python -m mymod func1`` to run only func1's doctest
* Use the command ``python -m mymod func2`` to run only func2's doctest

Lastly, by running the command ``xdoc.doctest_module(<pkgname>)``,
``xdoctest`` will recursively find and execute all doctests within the
modules belonging to the package.

Zero-args runner
^^^^^^^^^^^^^^^^

A benefit of using the native interface is the "zero-args" mode in the
``xdoctest`` runner. This allows you to run functions in your modules
via the command line as long as they take no arguments. The purpose is
to create a quick entry point to functions in your code (because
``xdoctest`` is taking the space in the ``__main__`` block).

For example, you might create a module ``mymod.py`` with the following
code:

.. code:: python

    def myfunc():
        print('hello world')

    if __name__ == '__main__':
        import xdoctest as xdoc
        xdoc.doctest_module(__file__)

Even though ``myfunc`` has no doctest it can still be run using the
command ``python -m mymod myfunc``.

Note, even though "zero-arg" functions can be run via this interface
they are not run by ``python -m mymod all``, nor are they listed by
``python -m mymod list``.

Enhancements
------------

The main enhancements ``xdoctest`` offers over ``doctest`` are:

1. All lines in the doctest can now be prefixed with ``>>>``. There is
   no need for the developer to differentiate between ``PS1`` and
   ``PS2`` lines. However, old-style doctests where ``PS2`` lines are
   prefixed with ``...`` are still valid.
2. Additionally, the multi-line strings don't require any prefix (but
   its ok if they do have either prefix).
3. Tests are executed in blocks, rather than line-by-line, thus
   comment-based directives (e.g. ``# doctest: +SKIP``) are now applied
   to an entire block, rather than just a single line.
4. Tests without a "want" statement will ignore any stdout / final
   evaluated value. This makes it easy to use simple assert statements
   to perform checks in code that might write to stdout.
5. If your test has a "want" statement and ends with both a value and
   stdout, both are checked, and the test will pass if either matches.
6. Ouptut from multiple sequential print statements can now be checked by
   a single "got" statement. (new in 0.4.0).

See code in ``_compare/compare.py`` and ``_compare/base_diff.py`` for a demo
that illustrates several of these enhancements. This demo mostly shows cases
where ``xdoctest`` works but ``doctest`` fails, but it does show **the only
corner case I can find** where ``doctest`` works but ``xdoctest`` does not.
Feel free to submit more in an issue if you can find any other backwards
incompatible cases.


Examples
--------

Here is an example demonstrating the new relaxed (and
backwards-compatible) syntax:

.. code:: python

    def func():
        """
        # Old way
        >>> def func():
        ...     print('The old regex-based parser required specific formatting')
        >>> func()
        The old regex-based parser required specific formatting

        # New way
        >>> def func():
        >>>     print('The new ast-based parser lets you prefix all lines with >>>')
        >>> func()
        The new ast-based parser lets you prefix all lines with >>>
        """

.. code:: python

    def func():
        """
        # Old way
        >>> print('''
        ... It would be nice if we didnt have to deal with prefixes
        ... in multiline strings.
        ... '''.strip())
        It would be nice if we didnt have to deal with prefixes
        in multiline strings.

        # New way
        >>> print('''
            Multiline can now be written without prefixes.
            Editing them is much more natural.
            '''.strip())
        Multiline can now be written without prefixes.
        Editing them is much more natural.

        # This is ok too
        >>> print('''
        >>> Just prefix everything with >>> and the doctest should work
        >>> '''.strip())
        Just prefix everything with >>> and the doctest should work

        """

Google style doctest support
----------------------------

Additionally, this module is written using
`Google-style <https://sphinxcontrib-napoleon.readthedocs.io>`__
docstrings, and as such, the module was originally written to directly
utilize them. However, for backwards compatibility and ease of
integration into existing software, the pytest plugin defaults to using
the more normal "freestyle" doctests that can be found anywhere in the
code.

To make use of Google-style docstrings, pytest can be run with the
option ``--xdoctest-style=google``, which causes xdoctest to only look
for doctests in Google "docblocks" with an ``Example:`` or ``Doctest:``
tag.

Notes on Got/Want tests
-----------------------

The new got/want tester is very permissive by default; it ignores
differences in whitespace, tries to normalize for python 2/3
Unicode/bytes differences, ANSI formatting, and it uses the old doctest
ELLIPSIS fuzzy matcher by default. If the "got" text matches the "want"
text at any point, the test passes.

Currently, this permissiveness is not highly configurable as it was in
the original doctest module. It is an open question as to whether or not
this module should support that level of configuration. If the test
requires a high degree of specificity in the got/want checker, it may
just be better to use an ``assert`` statement.

Backwards Compatibility
-----------------------
We (I) have removed all known backwards syntax incompatibilities. This is based
on running doctests on real life examples: ``boltons``, ``ubelt``, ``networkx``,
``pytorch`` (pending their acceptance of a pull-request), and on a set of
extensive self-testing. Please raise an issue or submit a merge/pull request.

Despite full syntax backwards compatibility, there are directive
incompatibilities by design. The directives we expose are more consise and
expressive. Our "got"/"want" checker is also much more permissive. We recommend
that you rely on coded ``assert``-statements for system-critical code. This also
makes it much easier to transform your ``xdoctest`` into a ``unittest`` when you
realize your doctests start getting too long.


.. |CircleCI| image:: https://circleci.com/gh/Erotemic/xdoctest.svg?style=svg
    :target: https://circleci.com/gh/Erotemic/xdoctest
.. |Travis| image:: https://img.shields.io/travis/Erotemic/xdoctest/master.svg?label=Travis%20CI
   :target: https://travis-ci.org/Erotemic/xdoctest
.. |Appveyor| image:: https://ci.appveyor.com/api/projects/status/github/Erotemic/xdoctest?branch=master&svg=True
   :target: https://ci.appveyor.com/project/Erotemic/xdoctest/branch/master
.. |Codecov| image:: https://codecov.io/github/Erotemic/xdoctest/badge.svg?branch=master&service=github
   :target: https://codecov.io/github/Erotemic/xdoctest?branch=master
.. |Pypi| image:: https://img.shields.io/pypi/v/xdoctest.svg
   :target: https://pypi.python.org/pypi/xdoctest
.. |Downloads| image:: https://img.shields.io/pypi/dm/xdoctest.svg
   :target: https://pypistats.org/packages/xdoctest
.. |ReadTheDocs| image:: https://readthedocs.org/projects/xdoctest/badge/?version=latest
    :target: https://xdoctest.readthedocs.io

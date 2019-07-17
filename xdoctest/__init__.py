# -*- coding: utf-8 -*-
"""

XDoctest - Extended Doctest
===========================

The ``xdoctest`` package is a re-write of Python's builtin ``doctest``
module. It replaces the old regex-based parser with a new
abstract-syntax-tree based parser (using Python's ``ast`` module). The
goal is to make doctests easier to write, simpler to configure, and
encourage the pattern of test driven development.


Getting Started
---------------

There are two ways to use ``xdoctest``: (1) ``pytest`` or (2) the native
interface. The native interface is less opaque and implicit, but its purpose is
to run doctests. The other option is to use the widely used ``pytest`` package.
This allows you to run both unit tests and doctests with the same command and
has many other advantages.

It is recommended to use ``pytest`` for automatic testing (e.g. in your CI
scripts), but for debugging it may be easier to use the native interface.

"""
# mkinit xdoctest --nomods
__version__ = '0.9.1'

# Expose only select submodules
__submodules__ = [
    'runner',
    'exceptions',
]


from xdoctest import utils
from xdoctest import docstr
from xdoctest.runner import (doctest_module,)
from xdoctest.exceptions import (DoctestParseError, ExitTestException,
                                 MalformedDocstr,)


__all__ = ['DoctestParseError', 'ExitTestException', 'MalformedDocstr',
           'doctest_module', 'utils', 'docstr', '__version__']

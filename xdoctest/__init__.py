# -*- coding: utf-8 -*-
"""
mkinit xdoctest --nomods
"""
__version__ = '0.6.2'  # nocover

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

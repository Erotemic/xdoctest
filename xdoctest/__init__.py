# -*- coding: utf-8 -*-
"""
mkinit xdoctest --nomods
"""
__version__ = '0.5.8'  # nocover

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


def add_line_numbers(source, start=1, n_digits=None):
    """
    Prefixes code with line numbers

    Example:
        >>> from xdoctest.utils.util_str import *
        >>> print(chr(10).join(add_line_numbers(['a', 'b', 'c'])))
        1 a
        2 b
        3 c
        >>> print(add_line_numbers(chr(10).join(['a', 'b', 'c'])))
        1 a
        2 b
        3 c
    """
    import math
    import six
    was_string = isinstance(source, six.string_types)
    part_lines = source.splitlines() if was_string else source

    if n_digits is None:
        endline = start + len(part_lines)
        n_digits = math.log(max(1, endline), 10)
        n_digits = int(math.ceil(n_digits))

    src_fmt = '{count:{n_digits}d} {line}'

    part_lines = [
        src_fmt.format(n_digits=n_digits, count=count, line=line)
        for count, line in enumerate(part_lines, start=start)
    ]

    if was_string:
        return '\n'.join(part_lines)
    else:
        return part_lines
setattr(utils, 'add_line_numbers', add_line_numbers)


__all__ = ['DoctestParseError', 'ExitTestException', 'MalformedDocstr',
           'doctest_module', 'utils', 'docstr', '__version__']

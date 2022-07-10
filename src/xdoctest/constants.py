# -*- coding: utf-8 -*-
"""
Defines sentinel values for internal xdoctest usage
"""
from __future__ import print_function, division, absolute_import, unicode_literals


# Create the most singleton object ever to avoid reload issues
# this is based on ubelt.NoParam, which has more docs on how this works
class _NOT_EVAL_TYPE(object):
    """
    This is a singleton object used as a sentinel value.  The value of
    :data:`NoParam` is robust to reloading, pickling, and copying.  See
    [SO_41048643]_ for more details.

    References:
        .. [SO_41048643]: http://stackoverflow.com/questions/41048643/a-second-none

    Example:
        >>> from xdoctest.constants import NOT_EVALED, _NOT_EVAL_TYPE  # NOQA
        >>> import copy
        >>> assert not NOT_EVALED
        >>> assert str(NOT_EVALED) == '<NOT_EVALED>'
        >>> assert repr(NOT_EVALED) == '<NOT_EVALED>'
        >>> assert NOT_EVALED(...) is None
        >>> assert copy.copy(NOT_EVALED) is NOT_EVALED
        >>> assert copy.deepcopy(NOT_EVALED) is NOT_EVALED
        >>> assert _NOT_EVAL_TYPE() is NOT_EVALED
    """
    def __new__(cls):
        return NOT_EVALED
    def __reduce__(self):
        return (_NOT_EVAL_TYPE, ())
    def __copy__(self):
        return NOT_EVALED
    def __deepcopy__(self, memo):
        return NOT_EVALED
    def __call__(self, default):
        pass
    def __str__(cls):
        return '<NOT_EVALED>'
    def __repr__(cls):
        return '<NOT_EVALED>'
    def __bool__(self):
        return False
    __nonzero__ = __bool__
try:
    NOT_EVALED  # type: ignore
except NameError:
    NOT_EVALED = object.__new__(_NOT_EVAL_TYPE)  # type: _NOT_EVAL_TYPE

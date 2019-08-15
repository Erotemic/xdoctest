# -*- coding: utf-8 -*-
"""
Defines sentinal values for internal xdoctest usage
"""
from __future__ import print_function, division, absolute_import, unicode_literals

if False:
    NOT_EVALED = object()  # nocover
else:
    # Create the most singleton object ever to avoid reload issues
    # see ubelt.NoParam for details on how thi works
    class _NOT_EVAL_TYPE(object):
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
        NOT_EVALED  # pragma: no cover
    except NameError:  # pragma: no cover
        NOT_EVALED = object.__new__(_NOT_EVAL_TYPE)  # pragma: no cover

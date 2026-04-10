"""
Port of NiceRepr from ubelt.util_mixins
"""

from __future__ import annotations

import warnings


class NiceRepr:
    """
    Defines `__str__` and `__repr__` in terms of `__nice__` function
    Classes that inherit `NiceRepr` must define `__nice__`

    Example:
        >>> class Foo(NiceRepr):
        ...    pass
        >>> class Bar(NiceRepr):
        ...    def __nice__(self):
        ...        return 'info'
        >>> foo = Foo()
        >>> bar = Bar()
        >>> assert str(bar) == '<Bar(info)>'
        >>> assert repr(bar).startswith('<Bar(info) at ')
        >>> assert 'object at' in str(foo)
        >>> assert 'object at' in repr(foo)
    """

    def __nice__(self) -> str:
        """
        Returns:
            str
        """
        if hasattr(self, '__len__'):
            # It is a common pattern for objects to use __len__ in __nice__
            # As a convenience we define a default __nice__ for these objects
            # return str(len(self))
            # hasattr doesn't narrow to Sized for ty, so call __len__ directly
            return str(self.__len__())  # type: ignore
        else:
            # In all other cases force the subclass to overload __nice__
            raise NotImplementedError(
                'Define the __nice__ method for {!r}'.format(self.__class__)
            )

    def __repr__(self) -> str:
        """
        Returns:
            str
        """
        try:
            nice = self.__nice__()
            classname = self.__class__.__name__
            return '<{0}({1}) at {2}>'.format(classname, nice, hex(id(self)))
        except Exception as ex:
            warnings.warn(str(ex), category=RuntimeWarning)
            return object.__repr__(self)

    def __str__(self) -> str:
        """
        Returns:
            str
        """
        try:
            classname = self.__class__.__name__
            nice = self.__nice__()
            return '<{0}({1})>'.format(classname, nice)
        except Exception as ex:
            warnings.warn(str(ex), category=RuntimeWarning)
            return object.__repr__(self)

"""
Port of NiceRepr from ubelt.util_mixins
"""

from __future__ import annotations


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
        Returns a string representation of the object's state.

        Subclasses must override this method to provide a custom
        string representation.

        Returns:
            str: A string describing the object's state.

        Raises:
            AttributeError: If the subclass has not implemented this method.
        """
        raise AttributeError(f'{self.__class__.__name__} must define __nice__')

    def __repr__(self) -> str:
        try:
            classname = self.__class__.__name__
            devnice = self.__nice__()
            return '<%s(%s) at %s>' % (classname, devnice, hex(id(self)))
        except AttributeError:
            if hasattr(self, '__nice__'):
                raise
            # warnings.warn('Define the __nice__ method for %r' %
            #               (self.__class__,), category=RuntimeWarning)
            return object.__repr__(self)
            # return super(NiceRepr, self).__repr__()

    def __str__(self) -> str:
        try:
            classname = self.__class__.__name__
            devnice = self.__nice__()
            return '<%s(%s)>' % (classname, devnice)
        except AttributeError:
            if hasattr(self, '__nice__'):
                raise
            # warnings.warn('Define the __nice__ method for %r' %
            #               (self.__class__,), category=RuntimeWarning)
            return object.__str__(self)
            # return super(NiceRepr, self).__str__()

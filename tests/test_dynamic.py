"""
This mod has a docstring

Example:
    >>> pass
"""
import sys
from xdoctest import dynamic_analysis as dynamic
from xdoctest import static_analysis as static

# add function from another module
is_defined_by_module = dynamic.is_defined_by_module
TopLevelVisitor = static.TopLevelVisitor


class SimpleDescriptor(object):
    def __init__(self):
        self.value = 0

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        self.value = float(value)


class SimpleClass(object):
    """
    Example:
        >>> pass
    """
    cls_attr = SimpleDescriptor()

    # Injected funcs should not be part of the calldefs
    visit = TopLevelVisitor.visit

    def __init__(self):
        self.inst_attr = SimpleDescriptor()
        def submethod1():
            """
            Example:
                >>> pass
            """
            pass

    @classmethod
    def method1(cls):
        """
        Example:
            >>> pass
        """
        pass

    @staticmethod
    def method2():
        """
        Example:
            >>> pass
        """
        pass

    @property
    def method3(self):
        """
        Example:
            >>> pass
        """
        pass

    def method4(self):
        """
        Example:
            >>> pass
        """
        pass


def simple_func1():
    """
    Example:
        >>> pass
    """
    pass


def test_parse_dynamic_calldefs():
    """
    CommandLine:
        python tests/test_dynamic.py test_parse_dynamic_calldefs
    """

    def subfunc():
        """
        Example:
            >>> pass
        """
        pass

    module = sys.modules[test_parse_dynamic_calldefs.__module__]
    modpath = module.__file__
    calldefs = dynamic.parse_dynamic_calldefs(modpath)
    keys = [
        '__doc__',
        'SimpleClass',
        'SimpleClass.method1',
        'SimpleClass.method2',
        'SimpleClass.method3',
        'SimpleClass.method4',
        'simple_func1',
    ]
    for key in keys:
        print('Check parsed key = {!r} in calldefs'.format(key))
        assert key in calldefs

    keys = [
        'foobar',
        'subfunc',
        'submethod1',
        'is_defined_by_module',
        'TopLevelVisitor',
        'SimpleClass.visit',
    ]
    for key in keys:
        print('Check parsed key = {!r} not in calldefs'.format(key))
        assert key not in calldefs

    assert 'visit' in dir(SimpleClass)
    assert 'is_defined_by_module' in dir(module)
    assert 'TopLevelVisitor' in dir(module)


def test_defined_by_module():
    """
    CommandLine:
        python tests/test_dynamic.py test_defined_by_module
    """
    module = sys.modules[test_defined_by_module.__module__]

    instance = SimpleClass()

    items = [
        SimpleClass,
        SimpleClass.method1,
        SimpleClass.method2,
        SimpleClass.method3,
        SimpleClass.method4,
        instance,
        instance.method1,
        instance.method2,
        instance.method4,
        instance.inst_attr,
    ]

    for item in items:
        flag = dynamic.is_defined_by_module(item, module)
        print('Checking {} is defined by {}'.format(item, module.__name__))
        assert flag, '{} should be defined by {}'.format(item, module)

    items = [
        sys, int, 0, 'foobar', module.__name__
    ]
    for item in items:
        flag = dynamic.is_defined_by_module(item, module)
        print('Checking {} is not defined by {}'.format(item, module.__name__))
        assert not flag, '{} should not be defined by {}'.format(item, module)

    import platform
    if platform.python_implementation() == 'PyPy':
        import pytest
        pytest.skip('ctypes for pypy')

    import _ctypes

    items = [
        _ctypes.Array,
        _ctypes.CFuncPtr,
        _ctypes.CFuncPtr.restype,
    ]
    module = _ctypes

    for item in items:
        flag = dynamic.is_defined_by_module(item, module)
        print('Checking {} is defined by {}'.format(item, module.__name__))
        assert flag, '{} should be defined by {}'.format(item, module)

    import six
    # Six brings in items from other modules

    items = [
        six.moves.zip,
        six.moves.range,
        six.moves.StringIO,
    ]
    module = six

    for item in items:
        flag = dynamic.is_defined_by_module(item, module)
        print('Checking {} is not defined by {}'.format(item, module.__name__))
        assert not flag, '{} should be not defined by {}'.format(item, module)


def test_programatically_generated_docstrings():
    """
    Test that the "dynamic" analysis mode works on dynamically generated
    docstrings.

    """
    from xdoctest import utils
    from xdoctest.utils.util_misc import TempModule
    temp = TempModule(utils.codeblock(
        '''
        code = ">>> print('hello world')"

        def func1():
            """
            Example:
                {}
            """

        func1.__doc__ = func1.__doc__.format(code)

        '''))

    import xdoctest
    # auto wont pick up dynamic doctests by default
    # Although in the future it would be cool if it did
    result = xdoctest.doctest_module(temp.modpath, analysis='auto', command='all')
    assert result['n_total'] == 1
    assert result['n_failed'] == 0

    # but an explicit dynamic should pick these up
    result = xdoctest.doctest_module(temp.modpath, analysis='dynamic', command='all')
    assert result['n_passed'] == 1
    assert result['n_failed'] == 0

    # module = ub.import_module_from_path(temp.modpath)
    # assert module.func1.__doc__ is not None
    # list(xdoctest.core.parse_doctestables(temp.modpath, analysis='dynamic'))
    # xdoctest.core.DEBUG = 1
    # calldefs = list(xdoctest.core.package_calldefs(temp.modpath, analysis='dynamic'))
    # calldefs = list(xdoctest.core.parse_calldefs(temp.modpath, analysis='dynamic'))
    # from xdoctest import dynamic_analysis
    # from xdoctest import static_analysis
    # static_analysis.parse_static_calldefs(fpath=temp.modpath)
    # node = dynamic_analysis.parse_dynamic_calldefs(temp.modpath)['func1']
    # node = dynamic_analysis.parse_dynamic_calldefs(temp.modpath)['func2']


if __name__ == '__main__':
    """
    CommandLine:
        python tests/test_dynamic.py
        pytest tests/test_dynamic.py
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

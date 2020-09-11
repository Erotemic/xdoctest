# -*- coding: utf-8 -*-
"""
Utilities for dynamically inspecting code
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import inspect
import os
import types
import six


def parse_dynamic_calldefs(modpath_or_module):
    """
    Dynamic parsing of module doctestable items.

    Unlike static parsing this forces execution of the module code before
    test-time, however the former is limited to plain-text python files whereas
    this can discover doctests in binary extension libraries.

    Args:
       modpath_or_module (str | Module): path to module or the module itself

    Returns:
        Dict[str, CallDefNode]:
            maping from callnames to CallDefNodes, which contain
               info about the item with the doctest.

    CommandLine:
        python -m xdoctest.dynamic_analysis parse_dynamic_calldefs

    Example:
        >>> from xdoctest import dynamic_analysis
        >>> module = dynamic_analysis
        >>> calldefs = parse_dynamic_calldefs(module.__file__)
        >>> for key, calldef in sorted(calldefs.items()):
        ...     print('key = {!r}'.format(key))
        ...     print(' * calldef.callname = {}'.format(calldef.callname))
        ...     if calldef.docstr is None:
        ...         print(' * len(calldef.docstr) = {}'.format(calldef.docstr))
        ...     else:
        ...         print(' * len(calldef.docstr) = {}'.format(len(calldef.docstr)))
    """
    from xdoctest import static_analysis as static

    import types
    if isinstance(modpath_or_module, types.ModuleType):
        module = modpath_or_module
    else:
        modpath = modpath_or_module
        if modpath.endswith('.ipynb'):
            """
            modpath = ub.expandpath("~/code/xdoctest/testing/notebook_with_doctests.ipynb")
            xdoctest ~/code/xdoctest/testing/notebook_with_doctests.ipynb
            """
            from xdoctest.utils import util_notebook
            module = util_notebook.import_notebook_from_path(modpath)
        else:
            # Possible option for dynamic parsing
            from xdoctest.utils import util_import
            module = util_import.import_module_from_path(modpath)

    calldefs = {}

    if getattr(module, '__doc__'):
        calldefs['__doc__'] = static.CallDefNode(
            callname='__doc__',
            docstr=module.__doc__,
            lineno=0,
            doclineno=1,
            doclineno_end=1,
            args=None
        )

    for key, val in iter_module_doctestables(module):
        # if hasattr(val, '__doc__'):
        if hasattr(val, '__doc__') and hasattr(val, '__name__'):
            calldefs[key] = static.CallDefNode(
                callname=val.__name__,
                docstr=val.__doc__,
                lineno=0,
                doclineno=1,
                doclineno_end=1,
                args=None
            )
    return calldefs


def get_stack_frame(n=0, strict=True):
    """
    Gets the current stack frame or any of its ancestors dynamically

    Args:
        n (int): n=0 means the frame you called this function in.
                 n=1 is the parent frame.
        strict (bool): (default = True)

    Returns:
        frame: frame_cur

    Example:
        >>> frame_cur = get_stack_frame(n=0)
        >>> print('frame_cur = %r' % (frame_cur,))
        >>> assert frame_cur.f_globals['frame_cur'] is frame_cur
    """
    frame_cur = inspect.currentframe()
    # Use n+1 to always skip the frame of this function
    for ix in range(n + 1):
        frame_next = frame_cur.f_back
        if frame_next is None:  # nocover
            if strict:
                raise AssertionError('Frame level %r is root' % ix)
            else:
                break
        frame_cur = frame_next
    return frame_cur


def get_parent_frame(n=0):
    """
    Returns the frame of that called you.
    This is equivalent to `get_stack_frame(n=1)`

    Args:
        n (int): n=0 means the frame you called this function in.
                 n=1 is the parent frame.

    Returns:
        frame: parent_frame

    Example:
        >>> root0 = get_stack_frame(n=0)
        >>> def foo():
        >>>     child = get_stack_frame(n=0)
        >>>     root1 = get_parent_frame(n=0)
        >>>     root2 = get_stack_frame(n=1)
        >>>     return child, root1, root2
        >>> # Note this wont work in IPython because several
        >>> # frames will be inserted between here and foo
        >>> child, root1, root2 = foo()
        >>> print('root0 = %r' % (root0,))
        >>> print('root1 = %r' % (root1,))
        >>> print('root2 = %r' % (root2,))
        >>> print('child = %r' % (child,))
        >>> assert root0 == root1
        >>> assert root1 == root2
        >>> assert child != root1
    """
    parent_frame = get_stack_frame(n=n + 2)
    return parent_frame


def iter_module_doctestables(module):
    r"""
    Yeilds doctestable objects that belong to a live python module

    Args:
        module (module): live python module

    Yeilds:
        tuple (str, callable): (funcname, func) doctestable

    CommandLine:
        python -m xdoctest.dynamic_analysis iter_module_doctestables

    Example:
        >>> from xdoctest import dynamic_analysis
        >>> module = dynamic_analysis
        >>> doctestable_list = list(iter_module_doctestables(module))
        >>> items = sorted([str(item) for item in doctestable_list])
        >>> print('[' + '\n'.join(items) + ']')
    """
    valid_func_types = (
        types.FunctionType,
        types.BuiltinFunctionType,
        types.MethodType,
        classmethod,
        staticmethod,
        property,
    )

    if six.PY2:
        valid_class_types = (types.ClassType,  types.TypeType,)
    else:
        valid_class_types = six.class_types

    def _recurse(item, module):
        return is_defined_by_module(item, module)

    #modpath = static.modpath_to_modname(module.__file__)
    for key, val in module.__dict__.items():
        if isinstance(val, valid_func_types):
            if not _recurse(val, module):
                continue
            yield key, val
        elif isinstance(val, valid_class_types):
            if not _recurse(val, module):
                continue
            # Yield the class itself
            yield key, val
            # Yield methods of the class
            for subkey, subval in six.iteritems(val.__dict__):
                # Unbound methods are still typed as functions
                if isinstance(subval, valid_func_types):
                    if not _recurse(subval, module):
                        continue
                    # unpack underlying function
                    if isinstance(subval, property):
                        item = subval.fget
                    elif isinstance(subval, staticmethod):
                        item = subval.__func__
                    elif isinstance(subval, classmethod):
                        item = subval.__func__
                    else:
                        item = subval
                    yield key + '.' + subkey, item


def _func_globals(func):
    if six.PY2:
        return getattr(func, 'func_globals')
    else:
        return getattr(func, '__globals__')


def is_defined_by_module(item, module):
    """
    Check if item is directly defined by a module.

    This check may not always work, especially for decorated functions.

    CommandLine:
        xdoctest -m xdoctest.dynamic_analysis is_defined_by_module

    Example:
        >>> from xdoctest import dynamic_analysis
        >>> item = dynamic_analysis.is_defined_by_module
        >>> module = dynamic_analysis
        >>> assert is_defined_by_module(item, module)
        >>> item = dynamic_analysis.six
        >>> assert not is_defined_by_module(item, module)
        >>> item = dynamic_analysis.six.print_
        >>> assert not is_defined_by_module(item, module)
        >>> assert not is_defined_by_module(print, module)
        >>> # xdoctest: +REQUIRES(CPython)
        >>> import _ctypes
        >>> item = _ctypes.Array
        >>> module = _ctypes
        >>> assert is_defined_by_module(item, module)
        >>> item = _ctypes.CFuncPtr.restype
        >>> module = _ctypes
        >>> assert is_defined_by_module(item, module)

    """
    from xdoctest import static_analysis as static
    target_modname = module.__name__

    # invalid_types = (int, float, list, tuple, set)
    # if isinstance(item, invalid_types) or isinstance(item, six.string_type):
    #     raise TypeError('can only test definitions for classes and functions')

    flag = False
    if isinstance(item, types.ModuleType):
        if not hasattr(item, '__file__'):
            try:
                # hack for cv2 and xfeatures2d
                name = static.modpath_to_modname(module.__file__)
                flag = name in str(item)
            except Exception:
                flag = False
        else:
            item_modpath = os.path.realpath(os.path.dirname(item.__file__))
            mod_fpath = module.__file__.replace('.pyc', '.py')
            if not mod_fpath.endswith('__init__.py'):
                flag = False
            else:
                modpath = os.path.realpath(os.path.dirname(mod_fpath))
                modpath = modpath.replace('.pyc', '.py')
                flag = item_modpath.startswith(modpath)
    else:
        # unwrap static/class/property methods
        if isinstance(item, property):
            item = item.fget
        if isinstance(item, staticmethod):
            item = item.__func__
        if isinstance(item, classmethod):
            item = item.__func__

        if getattr(item, '__module__', None) == target_modname:
            flag = True
        elif hasattr(item, '__objclass__'):
            # should we just unwrap objclass?
            parent = item.__objclass__
            if getattr(parent, '__module__', None) == target_modname:
                flag = True
        if not flag:
            try:
                item_modname = _func_globals(item)['__name__']
                if item_modname == target_modname:
                    flag = True
            except  AttributeError:
                pass
    return flag


if __name__ == '__main__':
    import xdoctest as xdoc
    xdoc.doctest_module()

# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import importlib


def import_module_from_name(modname):
    """
    Args:
        modname (str):  module name

    Returns:
        module: module

    CommandLine:
        python -m xdoctest.utils import_module_from_name

    Example:
        >>> # test with modules that wont be imported in normal circumstances
        >>> # todo write a test where we gaurentee this
        >>> modname_list = [
        >>>     'pickletools',
        >>>     'lib2to3.fixes.fix_apply',
        >>> ]
        >>> #assert not any(m in sys.modules for m in modname_list)
        >>> modules = [import_module_from_name(modname) for modname in modname_list]
        >>> assert [m.__name__ for m in modules] == modname_list
        >>> assert all(m in sys.modules for m in modname_list)
    """
    if True:
        # See if this fixes the Docker issue we saw but were unable to
        # reproduce on another environment. Either way its better to use the
        # standard importlib implementation than the one I wrote a long time
        # ago.
        module = importlib.import_module(modname)
    else:
        # The __import__ statment is weird
        if '.' in modname:
            fromlist = modname.split('.')[-1]
            fromlist_ = list(map(str, fromlist))  # needs to be ascii for python2.7
            module = __import__(modname, {}, {}, fromlist_, 0)
        else:
            module = __import__(modname, {}, {}, [], 0)
    return module


def import_module_from_path(modpath):
    """
    Args:
        modpath (str): path to the module

    References:
        https://stackoverflow.com/questions/67631/import-module-given-path

    Example:
        >>> from xdoctest import utils
        >>> modpath = utils.__file__.replace('.pyc', '.py')
        >>> module = import_module_from_path(modpath)
        >>> assert module is utils
    """
    # the importlib version doesnt work in pytest
    import xdoctest.static_analysis as static
    dpath, rel_modpath = static.split_modpath(modpath)
    modname = static.modpath_to_modname(modpath)
    try:
        with PythonPathContext(dpath):
            module = import_module_from_name(modname)
    except Exception:
        print('Failed to import modname={} with modpath={}'.format(
            modname, modpath))
        raise
    # TODO: use this implementation once pytest fixes importlib
    # if six.PY2:  # nocover
    #     import imp
    #     module = imp.load_source(modname, modpath)
    # elif sys.version_info[0:2] <= (3, 4):  # nocover
    #     assert sys.version_info[0:2] <= (3, 2), '3.0 to 3.2 is not supported'
    #     from importlib.machinery import SourceFileLoader
    #     module = SourceFileLoader(modname, modpath).load_module()
    # else:
    #     import importlib.util
    #     spec = importlib.util.spec_from_file_location(modname, modpath)
    #     module = importlib.util.module_from_spec(spec)
    #     spec.loader.exec_module(module)
    return module


class PythonPathContext(object):
    """
    Context for temporarily adding a dir to the PYTHONPATH. Used in testing

    Args:
        dpath (str): directory to insert into the PYTHONPATH
        index (int): position to add to. Typically either -1 or 0.

    Example:
        >>> with PythonPathContext('foo', -1):
        >>>     assert sys.path[-1] == 'foo'
        >>> assert sys.path[-1] != 'foo'
        >>> with PythonPathContext('bar', 0):
        >>>     assert sys.path[0] == 'bar'
        >>> assert sys.path[0] != 'bar'
    """
    def __init__(self, dpath, index=-1):
        self.dpath = dpath
        self.index = index

    def __enter__(self):
        if self.index < 0:
            self.index = len(sys.path) + self.index + 1
        sys.path.insert(self.index, self.dpath)

    def __exit__(self, type, value, trace):
        msg_parts = [
            'sys.path significantly changed while in PythonPathContext.'
        ]
        if len(sys.path) <= self.index:
            msg_parts.append(
                'len(sys.path) = {!r} but index is {!r}'.format(
                    len(sys.path), self.index))
            raise AssertionError('\n'.join(msg_parts))

        if sys.path[self.index] != self.dpath:
            msg_parts.append(
                'Expected {!r} at index {!r} but got {!r}'.format(
                    self.dpath, self.index, sys.path[self.index]
                ))
            try:
                real_index = sys.path.index(self.dpath)
                msg_parts.append('Expected dpath was at index {}'.format(real_index))
                msg_parts.append('This could indicate conflicting module namespaces')
            except IndexError:
                msg_parts.append('Expected dpath was not in sys.path')
            raise AssertionError('\n'.join(msg_parts))
        sys.path.pop(self.index)

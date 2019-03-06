# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import sys


def import_module_from_name(modname):
    """
    Imports a module from its string name (__name__)

    Args:
        modname (str):  module name

    Returns:
        module: module

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
        import importlib
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


def import_module_from_path(modpath, index=-1):
    """
    Imports a module via its path

    Args:
        modpath (PathLike): path to the module on disk or within a zipfile.

    Returns:
        module: the imported module

    References:
        https://stackoverflow.com/questions/67631/import-module-given-path

    Notes:
        If the module is part of a package, the package will be imported first.
        These modules may cause problems when reloading via IPython magic

        This can import a module from within a zipfile. To do this modpath
        should specify the path to the zipfile and the path to the module
        within that zipfile separated by a colon or pathsep.
        E.g. `/path/to/archive.zip:mymodule.py`

    Warning:
        It is best to use this with paths that will not conflict with
        previously existing modules.

        If the modpath conflicts with a previously existing module name. And
        the target module does imports of its own relative to this conflicting
        path. In this case, the module that was loaded first will win.

        For example if you try to import '/foo/bar/pkg/mod.py' from the folder
        structure:
          - foo/
            +- bar/
               +- pkg/
                  +  __init__.py
                  |- mod.py
                  |- helper.py

       If there exists another module named `pkg` already in sys.modules
       and mod.py does something like `from . import helper`, Python will
       assume helper belongs to the `pkg` module already in sys.modules.
       This can cause a NameError or worse --- a incorrect helper module.

    Example:
        >>> import xdoctest
        >>> modpath = xdoctest.__file__
        >>> module = import_module_from_path(modpath)
        >>> assert module is xdoctest

    Example:
        >>> # Test importing a module from within a zipfile
        >>> import zipfile
        >>> from xdoctest import utils
        >>> from os.path import join, expanduser
        >>> import os
        >>> dpath = expanduser('~/.cache/xdoctest')
        >>> dpath = utils.ensuredir(dpath)
        >>> #dpath = utils.TempDir().ensure()
        >>> # Write to an external module named bar
        >>> external_modpath = join(dpath, 'bar.py')
        >>> open(external_modpath, 'w').write('testvar = 1')
        >>> internal = 'folder/bar.py'
        >>> # Move the external bar module into a zipfile
        >>> zippath = join(dpath, 'myzip.zip')
        >>> with zipfile.ZipFile(zippath, 'w') as myzip:
        >>>     myzip.write(external_modpath, internal)
        >>> # Import the bar module from within the zipfile
        >>> modpath = zippath + ':' + internal
        >>> modpath = zippath + os.path.sep + internal
        >>> module = import_module_from_path(modpath)
        >>> assert module.__name__ == os.path.normpath('folder/bar')
        >>> assert module.testvar == 1

    Doctest:
        >>> import pytest
        >>> with pytest.raises(IOError):
        >>>     import_module_from_path('does-not-exist')
        >>> with pytest.raises(IOError):
        >>>     import_module_from_path('does-not-exist.zip/')
    """
    import os
    if not os.path.exists(modpath):
        import re
        import zipimport
        # We allow (if not prefer or force) the colon to be a path.sep in order
        # to agree with the mod.__name__ attribute that will be produced

        # zip followed by colon or slash
        pat = '(.zip[' + re.escape(os.path.sep) + '/:])'
        parts = re.split(pat, modpath, flags=re.IGNORECASE)
        if len(parts) > 2:
            archivepath = ''.join(parts[:-1])[:-1]
            internal = parts[-1]
            modname = os.path.splitext(internal)[0]
            modname = os.path.normpath(modname)
            if os.path.exists(archivepath):
                zimp_file = zipimport.zipimporter(archivepath)
                module = zimp_file.load_module(modname)
                return module
        raise IOError('modpath={} does not exist'.format(modpath))
    else:
        # the importlib version doesnt work in pytest
        module = _custom_import_modpath(modpath)
        # TODO: use this implementation once pytest fixes importlib
        # module = _pkgutil_import_modpath(modpath)
        return module


def _custom_import_modpath(modpath, index=-1):
    from xdoctest.static_analysis import split_modpath, modpath_to_modname
    dpath, rel_modpath = split_modpath(modpath)
    modname = modpath_to_modname(modpath)
    try:
        with PythonPathContext(dpath, index=index):
            module = import_module_from_name(modname)
    except Exception:  # nocover
        print('Failed to import modname={} with modpath={}'.format(
            modname, modpath))
        raise
    return module


def _pkgutil_import_modpath(modpath):  # nocover
    import six
    from xdoctest.static_analysis import split_modpath, modpath_to_modname
    dpath, rel_modpath = split_modpath(modpath)
    modname = modpath_to_modname(modpath)
    if six.PY2:  # nocover
        import imp
        module = imp.load_source(modname, modpath)
    elif sys.version_info[0:2] <= (3, 4):  # nocover
        assert sys.version_info[0:2] <= (3, 2), '3.0 to 3.2 is not supported'
        from importlib.machinery import SourceFileLoader
        module = SourceFileLoader(modname, modpath).load_module()
    else:
        import importlib.util
        spec = importlib.util.spec_from_file_location(modname, modpath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
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
        if len(sys.path) <= self.index:  # nocover
            msg_parts.append(
                'len(sys.path) = {!r} but index is {!r}'.format(
                    len(sys.path), self.index))
            raise AssertionError('\n'.join(msg_parts))

        if sys.path[self.index] != self.dpath:  # nocover
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

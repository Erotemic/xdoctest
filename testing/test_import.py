# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from os.path import join
import itertools as it
import sys
import pytest
from xdoctest import static_analysis as static
from xdoctest import utils


def touch(args):
    path = join(*args)
    with open(path, 'w') as file:
        file.write('')
    return path


def _static_modname_to_modpath(modname, **kwargs):
    # Calls static.modname_to_modpath with checks
    had = modname in sys.modules
    try:
        modpath = static.modname_to_modpath(modname, **kwargs)
    except ValueError:
        modpath = None
    if not had:
        assert modname not in sys.modules, (
            '{} should not be imported'.format(modname))
    return modpath


def test_modname_to_modpath_package():
    """
    CommandLine:
        pytest testing/test_static.py::test_modname_to_modpath_package

    Ignore:
        import sys
        sys.path.append('/home/joncrall/code/xdoctest/testing')
        from test_static import *
        temp = utils.TempDir()
        temp.__enter__()
        sys.path.append(temp.dpath)

        temp.__exit__(None, None, None)
    """
    with utils.TempDir() as temp:
        dpath = temp.dpath

        # Create a dummy package heirachy
        root = utils.ensuredir((dpath, '_tmproot'))
        sub1 = utils.ensuredir((root, 'sub1'))
        sub2 = utils.ensuredir((sub1, 'sub2'))

        root_init = touch((root, '__init__.py'))
        sub1_init = touch((sub1, '__init__.py'))
        sub2_init = touch((sub2, '__init__.py'))

        mod0 = touch((root, 'mod0.py'))
        mod1 = touch((sub1, 'mod1.py'))
        mod2 = touch((sub2, 'mod2.py'))

        root_main = touch((root, '__main__.py'))
        sub2_main = touch((sub2, '__main__.py'))

        bad1 = utils.ensuredir((root, 'bad1'))
        bad2 = utils.ensuredir((sub1, 'bad2'))
        touch((bad1, 'b0.py'))
        touch((bad2, 'b0.py'))

        with utils.PythonPathContext(dpath):
            # Bad module directories should return None
            assert _static_modname_to_modpath('_tmproot.bad1') is None
            assert _static_modname_to_modpath('_tmproot.sub1.bad1') is None
            assert _static_modname_to_modpath('_tmproot.bad1.b0') is None
            assert _static_modname_to_modpath('_tmproot.sub1.bad1.b1') is None
            assert _static_modname_to_modpath('_tmproot.bad1') is None

            # package modules are accessable by the full path
            assert root == _static_modname_to_modpath('_tmproot')
            assert sub1 == _static_modname_to_modpath('_tmproot.sub1')
            assert sub2 == _static_modname_to_modpath('_tmproot.sub1.sub2')
            assert mod0 == _static_modname_to_modpath('_tmproot.mod0')
            assert mod1 == _static_modname_to_modpath('_tmproot.sub1.mod1')
            assert mod2 == _static_modname_to_modpath('_tmproot.sub1.sub2.mod2')

            # specifying a suffix will not work
            assert _static_modname_to_modpath('sub1') is None
            assert _static_modname_to_modpath('sub1.sub2') is None
            assert _static_modname_to_modpath('mod0') is None
            assert _static_modname_to_modpath('sub1.mod1') is None
            assert _static_modname_to_modpath('sub1.sub2.mod2') is None

            # Specify init if available
            assert root_init == _static_modname_to_modpath('_tmproot', hide_init=False)

            if 1:
                # Test init
                assert _static_modname_to_modpath('_tmproot', hide_init=False) == root_init
                assert _static_modname_to_modpath('_tmproot.__init__', hide_init=False) == root_init
                assert _static_modname_to_modpath('_tmproot.__main__', hide_init=False, hide_main=True) == root

                # Test main
                assert _static_modname_to_modpath('_tmproot', hide_main=False) == root
                assert _static_modname_to_modpath('_tmproot.__init__', hide_main=False) == root
                assert _static_modname_to_modpath('_tmproot.__main__', hide_main=False) == root_main

                # Test init and main both false
                assert _static_modname_to_modpath('_tmproot.__init__') == root
                assert _static_modname_to_modpath('_tmproot.__main__', hide_main=True) == root

                # Test init and main both true
                assert _static_modname_to_modpath('_tmproot', hide_init=False, hide_main=False) == root_init
                assert _static_modname_to_modpath('_tmproot.__init__', hide_init=False, hide_main=False) == root_init
                assert _static_modname_to_modpath('_tmproot.__main__', hide_init=False, hide_main=False) == root_main

            if 2:
                # Test in a nested directory
                # Test init
                assert _static_modname_to_modpath('_tmproot.sub1.sub2', hide_init=False) == sub2_init
                assert _static_modname_to_modpath('_tmproot.sub1.sub2.__init__', hide_init=False) == sub2_init
                assert _static_modname_to_modpath('_tmproot.sub1.sub2.__main__', hide_init=False, hide_main=True) == sub2

                # Test main
                assert _static_modname_to_modpath('_tmproot.sub1.sub2', hide_main=False) == sub2
                assert _static_modname_to_modpath('_tmproot.sub1.sub2.__main__', hide_main=False) == sub2_main
                assert _static_modname_to_modpath('_tmproot.sub1.sub2.__init__', hide_main=False) == sub2

                # Test init and main both false
                assert _static_modname_to_modpath('_tmproot.sub1.sub2.__init__', hide_main=True) == sub2
                assert _static_modname_to_modpath('_tmproot.sub1.sub2.__main__', hide_main=True) == sub2

                # Test init and main both true
                assert _static_modname_to_modpath('_tmproot.sub1.sub2', hide_init=False, hide_main=False) == sub2_init
                assert _static_modname_to_modpath('_tmproot.sub1.sub2.__init__', hide_init=False, hide_main=False) == sub2_init
                assert _static_modname_to_modpath('_tmproot.sub1.sub2.__main__', hide_init=False, hide_main=False) == sub2_main

            if 3:
                # Test in a nested directory with __init__ but no __main__
                # Test init
                assert _static_modname_to_modpath('_tmproot.sub1', hide_init=False) == sub1_init
                assert _static_modname_to_modpath('_tmproot.sub1.__init__', hide_init=False) == sub1_init
                assert _static_modname_to_modpath('_tmproot.sub1.__main__', hide_init=False) is None

                # Test main
                assert _static_modname_to_modpath('_tmproot.sub1', hide_main=False) == sub1
                assert _static_modname_to_modpath('_tmproot.sub1.__main__', hide_main=False) is None
                assert _static_modname_to_modpath('_tmproot.sub1.__init__', hide_main=False) == sub1

                # Test init and main both false
                assert _static_modname_to_modpath('_tmproot.sub1.__init__') == sub1
                assert _static_modname_to_modpath('_tmproot.sub1.__main__') is None

                # Test init and main both true
                assert _static_modname_to_modpath('_tmproot.sub1', hide_init=False, hide_main=False) == sub1_init
                assert _static_modname_to_modpath('_tmproot.sub1.__init__', hide_init=False, hide_main=False) == sub1_init
                assert _static_modname_to_modpath('_tmproot.sub1.__main__', hide_init=False, hide_main=False) is None

            assert '_tmproot' not in sys.modules
            assert '_tmproot.mod0' not in sys.modules
            assert '_tmproot.sub1' not in sys.modules
            assert '_tmproot.sub1.mod1' not in sys.modules
            assert '_tmproot.sub1.sub2' not in sys.modules
            assert '_tmproot.sub1.mod2.mod2' not in sys.modules


def test_modname_to_modpath_single():
    with utils.TempDir() as temp:
        dpath = temp.dpath

        # Single module
        single = touch((dpath, '_tmpsingle.py'))
        single_main = touch((dpath, '__main__.py'))

        with utils.PythonPathContext(dpath):
            assert single == _static_modname_to_modpath('_tmpsingle')
            assert single == _static_modname_to_modpath('_tmpsingle', hide_init=True, hide_main=False)
            assert single == _static_modname_to_modpath('_tmpsingle', hide_init=False, hide_main=False)
            assert single == _static_modname_to_modpath('_tmpsingle', hide_init=False, hide_main=True)

            # Weird module named main not in a package
            assert _static_modname_to_modpath('__main__') == single_main
            assert _static_modname_to_modpath('__main__', hide_init=True, hide_main=False) == single_main
            assert _static_modname_to_modpath('__main__', hide_init=False, hide_main=False) == single_main
            assert _static_modname_to_modpath('__main__', hide_init=False, hide_main=True) == single_main


def test_modname_to_modpath_namespace():
    """
    Ignore:
        import sys
        sys.path.append('/home/joncrall/code/xdoctest/testing')
        from test_static import *
        temp = utils.TempDir()
        temp.__enter__()
        sys.path.append(temp.dpath)

        temp.__exit__(None, None, None)

    %timeit _syspath_modname_to_modpath('xdoctest.static_analysis')
    %timeit _pkgutil_modname_to_modpath('xdoctest.static_analysis')
    """
    with utils.TempDir() as temp:
        dpath = temp.dpath

        # Some "bad" non-module directories
        tmpbad = utils.ensuredir((dpath, '_tmpbad'))

        # Make a submodule of a bad directory, look good.
        sub_bad = utils.ensuredir((tmpbad, 'sub_bad'))
        touch((tmpbad, '_inbad.py'))
        subbad = touch((sub_bad, '__init__.py'))  # NOQA
        b0 = touch((sub_bad, 'b0.py'))  # NOQA

        with utils.PythonPathContext(dpath):
            assert _static_modname_to_modpath('_tmpbad') is None

            # Tricky case, these modules look good outside of _tmpbad WOW, you
            # can actually import this and it works, but pkgloader still
            # returns None so we should too.
            assert _static_modname_to_modpath('_tmpbad.sub_bad') is None
            assert _static_modname_to_modpath('_tmpbad.sub_bad.b0') is None

            # We should be able to statically find all of the good module
            # directories.

            # this should all be static
            import sys
            assert '_tmpsingle' not in sys.modules
            assert '_tmpbad' not in sys.modules


def test_package_submodules():
    """
    CommandLine:
        pytest testing/test_static.py::test_package_submodules -s
        pass

    Ignore:
        import sys
        sys.path.append('/home/joncrall/code/xdoctest/testing')
        from test_static import *
        temp = utils.TempDir()
        temp.__enter__()
        sys.path.append(temp.dpath)

        temp.__exit__(None, None, None)
    """
    with utils.TempDir() as temp:
        dpath = temp.dpath

        # Create a dummy package heirachy
        root = utils.ensuredir((dpath, '_tmproot'))
        sub1 = utils.ensuredir((root, 'sub1'))
        sub2 = utils.ensuredir((sub1, 'sub2'))

        root_init = touch((root, '__init__.py'))
        sub1_init = touch((sub1, '__init__.py'))
        sub2_init = touch((sub2, '__init__.py'))

        mod0 = touch((root, 'mod0.py'))
        mod1 = touch((sub1, 'mod1.py'))
        mod2 = touch((sub2, 'mod2.py'))

        root_main = touch((root, '__main__.py'))
        sub2_main = touch((sub2, '__main__.py'))

        bad1 = utils.ensuredir((root, 'bad1'))
        bad2 = utils.ensuredir((sub1, 'bad2'))
        b0 = touch((bad1, 'b0.py'))
        b1 = touch((bad2, 'b1.py'))

        with utils.PythonPathContext(dpath):
            subpaths = sorted(static.package_modpaths(root, with_pkg=True))

            # should only return files not directories
            assert root_init in subpaths
            assert sub1_init in subpaths
            assert sub2_init in subpaths
            assert root not in subpaths
            assert sub1 not in subpaths
            assert sub2 not in subpaths

            assert root_main in subpaths
            assert sub2_main in subpaths

            assert mod0 in subpaths
            assert mod1 in subpaths
            assert mod2 in subpaths

            assert bad1 not in subpaths
            assert b0 not in subpaths
            assert b1 not in subpaths

            assert '_tmproot' not in sys.modules
            assert '_tmproot.mod0' not in sys.modules
            assert '_tmproot.sub1' not in sys.modules
            assert '_tmproot.sub1.mod1' not in sys.modules
            assert '_tmproot.sub1.sub2' not in sys.modules
            assert '_tmproot.sub1.mod2.mod2' not in sys.modules


def test_modpath_to_modname():
    """
    CommandLine:
        pytest testing/test_static.py::test_modpath_to_modname -s
        python testing/test_static.py test_modpath_to_modname
    """
    with utils.TempDir() as temp:
        dpath = temp.dpath

        # Create a dummy package heirachy
        root = utils.ensuredir((dpath, '_tmproot'))
        sub1 = utils.ensuredir((root, 'sub1'))
        sub2 = utils.ensuredir((sub1, 'sub2'))

        root_init = touch((root, '__init__.py'))
        sub1_init = touch((sub1, '__init__.py'))
        sub2_init = touch((sub2, '__init__.py'))

        mod0 = touch((root, 'mod0.py'))
        mod1 = touch((sub1, 'mod1.py'))
        mod2 = touch((sub2, 'mod2.py'))

        root_main = touch((root, '__main__.py'))
        sub2_main = touch((sub2, '__main__.py'))

        bad1 = utils.ensuredir((root, 'bad1'))
        bad2 = utils.ensuredir((sub1, 'bad2'))
        b0 = touch((bad1, 'b0.py'))
        b1 = touch((bad2, 'b1.py'))

        with utils.PythonPathContext(dpath):

            assert static.modpath_to_modname(root) == '_tmproot'
            assert static.modpath_to_modname(sub1) == '_tmproot.sub1'
            assert static.modpath_to_modname(sub2) == '_tmproot.sub1.sub2'

            assert static.modpath_to_modname(mod0) == '_tmproot.mod0'
            assert static.modpath_to_modname(mod1) == '_tmproot.sub1.mod1'
            assert static.modpath_to_modname(mod2) == '_tmproot.sub1.sub2.mod2'

            assert static.modpath_to_modname(root_init) == '_tmproot'
            assert static.modpath_to_modname(sub1_init) == '_tmproot.sub1'
            assert static.modpath_to_modname(sub2_init) == '_tmproot.sub1.sub2'

            assert static.modpath_to_modname(root_init, hide_init=False) == '_tmproot.__init__'
            assert static.modpath_to_modname(sub1_init, hide_init=False) == '_tmproot.sub1.__init__'
            assert static.modpath_to_modname(sub2_init, hide_init=False) == '_tmproot.sub1.sub2.__init__'

            assert static.modpath_to_modname(root, hide_main=True, hide_init=False) == '_tmproot.__init__'
            assert static.modpath_to_modname(sub1, hide_main=True, hide_init=False) == '_tmproot.sub1.__init__'
            assert static.modpath_to_modname(sub2, hide_main=True, hide_init=False) == '_tmproot.sub1.sub2.__init__'

            assert static.modpath_to_modname(root, hide_main=False, hide_init=False) == '_tmproot.__init__'
            assert static.modpath_to_modname(sub1, hide_main=False, hide_init=False) == '_tmproot.sub1.__init__'
            assert static.modpath_to_modname(sub2, hide_main=False, hide_init=False) == '_tmproot.sub1.sub2.__init__'

            assert static.modpath_to_modname(root, hide_main=False, hide_init=True) == '_tmproot'
            assert static.modpath_to_modname(sub1, hide_main=False, hide_init=True) == '_tmproot.sub1'
            assert static.modpath_to_modname(sub2, hide_main=False, hide_init=True) == '_tmproot.sub1.sub2'

            assert static.modpath_to_modname(root_main, hide_main=False, hide_init=True) == '_tmproot.__main__'
            assert static.modpath_to_modname(sub2_main, hide_main=False, hide_init=True) == '_tmproot.sub1.sub2.__main__'

            assert static.modpath_to_modname(root_main, hide_main=False, hide_init=True) == '_tmproot.__main__'
            assert static.modpath_to_modname(sub2_main, hide_main=False, hide_init=True) == '_tmproot.sub1.sub2.__main__'

            assert static.modpath_to_modname(root_main, hide_main=True, hide_init=True) == '_tmproot'
            assert static.modpath_to_modname(sub2_main, hide_main=True, hide_init=True) == '_tmproot.sub1.sub2'

            assert static.modpath_to_modname(root_main, hide_main=True, hide_init=False) == '_tmproot'
            assert static.modpath_to_modname(sub2_main, hide_main=True, hide_init=False) == '_tmproot.sub1.sub2'

            # Non-existant / invalid modules should always be None
            for a, b in it.product([True, False], [True, False]):
                with pytest.raises(ValueError):
                    static.modpath_to_modname(join(sub1, '__main__.py'), hide_main=a, hide_init=b)
                assert static.modpath_to_modname(b0, hide_main=a, hide_init=b) == 'b0'
                assert static.modpath_to_modname(b1, hide_main=a, hide_init=b) == 'b1'
                with pytest.raises(ValueError):
                    static.modpath_to_modname(bad1, hide_main=a, hide_init=b)
                with pytest.raises(ValueError):
                    static.modpath_to_modname(bad2, hide_main=a, hide_init=b)

            assert '_tmproot' not in sys.modules
            assert '_tmproot.mod0' not in sys.modules
            assert '_tmproot.sub1' not in sys.modules
            assert '_tmproot.sub1.mod1' not in sys.modules
            assert '_tmproot.sub1.sub2' not in sys.modules
            assert '_tmproot.sub1.mod2.mod2' not in sys.modules

# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import os
import sys
import ast
import re
import tokenize
import six
from six.moves import cStringIO as StringIO
from collections import deque, OrderedDict
from xdoctest import utils
from os.path import (join, exists, expanduser, abspath, split, splitext,
                     isfile, dirname, basename, isdir)


class CallDefNode(object):
    def __init__(self, callname, lineno, docstr, doclineno, doclineno_end):
        self.callname = callname
        self.lineno = lineno
        self.docstr = docstr
        self.doclineno = doclineno
        self.doclineno_end = doclineno_end
        self.lineno_end = None

    # def __str__(self):
    #     return '{}[{}:{}][{}]'.format(
    #         self.callname, self.lineno, self.lineno_end,
    #         self.doclineno)


class TopLevelVisitor(ast.NodeVisitor):
    """
    Parses top-level function names and docstrings

    References:
        # For other visit_<classname> values see
        http://greentreesnakes.readthedocs.io/en/latest/nodes.html

    Example:
        >>> from xdoctest.static_analysis import *  # NOQA
        >>> from xdoctest import utils
        >>> source = utils.codeblock(
        ...    '''
        ...    def foo():
        ...        \"\"\" my docstring \"\"\"
        ...        def subfunc():
        ...            pass
        ...    def bar():
        ...        pass
        ...    class Spam(object):
        ...        def eggs():
        ...            pass
        ...    ''')
        >>> self = TopLevelVisitor.parse(source)
        >>> callnames = set(self.calldefs.keys())
        >>> assert callnames == {'foo', 'bar', 'Spam', 'Spam.eggs'}
        >>> assert self.calldefs['foo'].docstr.strip() == 'my docstring'
        >>> assert 'subfunc' not in self.calldefs
    """
    def __init__(self):
        super(TopLevelVisitor, self).__init__()
        self.calldefs = OrderedDict()
        self.sourcelines = None

        self._current_classname = None
        # Keep track of when we leave a top level definition
        self._finish_queue = deque()

        # new
        self.assignments = []

    def process_finished(self, node):
        """ process (get ending lineno) for everything marked as finished """
        if self._finish_queue:
            if isinstance(node, int):
                lineno_end = node
            else:
                lineno_end = getattr(node, 'lineno', None)
            while self._finish_queue:
                calldef = self._finish_queue.pop()
                calldef.lineno_end = lineno_end

    @classmethod
    def parse(TopLevelVisitor, source):
        self = TopLevelVisitor()
        self.sourcelines = source.splitlines()

        source_utf8 = source.encode('utf8')
        pt = ast.parse(source_utf8)

        self.visit(pt)

        lineno_end = source.count('\n') + 2  # one indexing
        self.process_finished(lineno_end)
        return self

    def visit(self, node):
        self.process_finished(node)
        super(TopLevelVisitor, self).visit(node)

    def visit_FunctionDef(self, node):
        if self._current_classname is None:
            callname = node.name
        else:
            callname = self._current_classname + '.' + node.name

        lineno = self._workaround_func_lineno(node)
        docstr, doclineno, doclineno_end = self._get_docstring(node)
        calldef = CallDefNode(callname, lineno, docstr, doclineno,
                              doclineno_end)
        self.calldefs[callname] = calldef

        self._finish_queue.append(calldef)

    def visit_ClassDef(self, node):
        if self._current_classname is None:
            callname = node.name
            self._current_classname = callname
            docstr, doclineno, doclineno_end = self._get_docstring(node)
            calldef = CallDefNode(callname, node.lineno, docstr, doclineno,
                                  doclineno_end)
            self.calldefs[callname] = calldef

            self.generic_visit(node)
            self._current_classname = None

            self._finish_queue.append(calldef)

    def visit_Module(self, node):
        # get the module level docstr
        docstr, doclineno, doclineno_end = self._get_docstring(node)
        if docstr:
            # the module level docstr is not really a calldef, but parse it for
            # backwards compatibility.
            callname = '__doc__'
            calldef = CallDefNode(callname, doclineno, docstr, doclineno,
                                  doclineno_end)
            self.calldefs[callname] = calldef

        self.generic_visit(node)
        # self._finish_queue.append(calldef)

    def visit_Assign(self, node):
        # print('VISIT FunctionDef node = %r' % (node,))
        # print('VISIT FunctionDef node = %r' % (node.__dict__,))
        if self._current_classname is None:
            for target in node.targets:
                if hasattr(target, 'id'):
                    self.assignments.append(target.id)
            # print('node.value = %r' % (node.value,))
            # TODO: assign constants to
            # self.const_lookup
        self.generic_visit(node)

    def visit_If(self, node):
        if isinstance(node.test, ast.Compare):  # pragma: nobranch
            try:
                if all([
                    isinstance(node.test.ops[0], ast.Eq),
                    node.test.left.id == '__name__',
                    node.test.comparators[0].s == '__main__',
                ]):
                    # Ignore main block
                    return
            except Exception:  # nocover
                pass
        self.generic_visit(node)  # nocover

    # def visit_ExceptHandler(self, node):
    #     pass

    # def visit_TryFinally(self, node):
    #     pass

    # def visit_TryExcept(self, node):
    #     pass

    # def visit_Try(self, node):
    #     TODO: parse a node only if it is visible in all cases
    #     pass
    #     # self.generic_visit(node)  # nocover

    # -- helpers ---

    def _docstr_line_workaround(self, docnode):
        # lineno points to the last line of a string
        endpos = docnode.lineno - 1
        # First assume we have a single quoted string
        startpos = endpos
        # See if we can check for the tripple quote
        # This is a hueristic, and is not robust
        trips = ('"""', "'''")
        endline = self.sourcelines[endpos]
        for trip in trips:
            # try to account for comments
            endline = re.sub(endline, trip + '\s*#.*$', trip).strip()
            if endline.endswith(trip):
                # Hack: we can count the number of lines in the str, but we can
                # be 100% sure that its a multiline string
                #
                # there are pathological cases this wont work for
                # (i.e. think nestings: """ # ''' # """)
                nlines = utils.ensure_unicode(docnode.value.s).count('\n')
                startline = self.sourcelines[endpos - nlines]
                if not startline.strip().startswith(trip):
                    startpos = endpos - nlines

        doclineno = startpos + 1
        doclineno_end = endpos + 2
        return doclineno, doclineno_end

    def _get_docstring(self, node):
        docstr = ast.get_docstring(node, clean=False)
        if docstr is not None:
            docnode = node.body[0]
            doclineno, doclineno_end = self._docstr_line_workaround(docnode)
        else:
            doclineno = None
            doclineno_end = None
        return (docstr, doclineno, doclineno_end)

    def _workaround_func_lineno(self, node):
        # Try and find the lineno of the function definition
        # (maybe the fact that its on a decorator is actually right...)
        if node.decorator_list:
            # Decorators can throw off the line the function is declared on
            lineno = node.lineno - 1
            pattern = '\s*def\s*' + node.name
            # I think this is actually robust
            while not re.match(pattern, self.sourcelines[lineno]):
                lineno += 1
            lineno += 1
        else:
            lineno = node.lineno
        return lineno


def parse_calldefs(source=None, fpath=None):
    r"""
    Statically finds top-level callable functions and methods in python source

    Args:
        source (str): python text
        fpath (str): filepath to read if source is not specified

    Returns:
        dict(str, CallDefNode): map of callnames to tuples with def info

    Example:
        >>> from xdoctest import static_analysis
        >>> fpath = static_analysis.__file__.replace('.pyc', '.py')
        >>> calldefs = parse_calldefs(fpath=fpath)
        >>> assert 'parse_calldefs' in calldefs
    """
    if source is None:  # pragma: no branch
        with open(fpath, 'rb') as file_:
            source = file_.read().decode('utf-8')
    try:
        self = TopLevelVisitor.parse(source)
        return self.calldefs
    except Exception:  # nocover
        if fpath:
            print('Failed to parse docstring for fpath=%r' % (fpath,))
        else:
            print('Failed to parse docstring')
        raise


def _parse_static_node_value(node):
    """
    Extract a constant value from a node if possible
    """
    if isinstance(node, ast.Num):
        value = node.n
    elif isinstance(node, ast.Str):
        value = node.s
    elif isinstance(node, ast.List):
        value = list(map(_parse_static_node_value, node.elts))
    elif isinstance(node, ast.Tuple):
        value = tuple(map(_parse_static_node_value, node.elts))
    elif isinstance(node, (ast.Dict)):
        keys = map(_parse_static_node_value, node.keys)
        values = map(_parse_static_node_value, node.values)
        value = dict(zip(keys, values))
    else:
        raise TypeError('Cannot parse a static value from non-static node '
                        'of type: {!r}'.format(type(node)))
    return value


def parse_static_value(key, source=None, fpath=None):
    """
    Statically parse a constant variable's value from python code.

    TODO: This does not belong here. Move this to an external static analysis
    library.

    Args:
        key (str): name of the variable
        source (str): python text
        fpath (str): filepath to read if source is not specified

    Example:
        >>> from xdoctest.static_analysis import parse_static_value
        >>> key = 'foo'
        >>> source = 'foo = 123'
        >>> assert parse_static_value(key, source=source) == 123
        >>> source = 'foo = "123"'
        >>> assert parse_static_value(key, source=source) == '123'
        >>> source = 'foo = [1, 2, 3]'
        >>> assert parse_static_value(key, source=source) == [1, 2, 3]
        >>> source = 'foo = (1, 2, "3")'
        >>> assert parse_static_value(key, source=source) == (1, 2, "3")
        >>> source = 'foo = {1: 2, 3: 4}'
        >>> assert parse_static_value(key, source=source) == {1: 2, 3: 4}
        >>> #parse_static_value('bar', source=source)
        >>> #parse_static_value('bar', source='foo=1; bar = [1, foo]')
    """
    if source is None:  # pragma: no branch
        with open(fpath, 'rb') as file_:
            source = file_.read().decode('utf-8')
    pt = ast.parse(source)

    class AssignentVisitor(ast.NodeVisitor):
        def visit_Assign(self, node):
            for target in node.targets:
                if getattr(target, 'id', None) == key:
                    self.value = _parse_static_node_value(node.value)

    sentinal = object()
    visitor = AssignentVisitor()
    visitor.value = sentinal
    visitor.visit(pt)
    if visitor.value is sentinal:
        raise NameError('No static variable named {!r}'.format(key))
    return visitor.value


def _platform_pylib_ext():  # nocover
    if sys.platform.startswith('linux'):  # nocover
        pylib_ext = '.so'
    elif sys.platform.startswith('win32'):  # nocover
        pylib_ext = '.pyd'
    elif sys.platform.startswith('darwin'):  # nocover
        pylib_ext = '.dylib'
    else:
        pylib_ext = '.so'
    return pylib_ext


# def package_modnames(package_name, with_pkg=False, with_mod=True):
#     pkgpath = modname_to_modpath(package_name)
#     for modpath in package_modpaths(pkgpath):
#         modname = modpath_to_modname(modpath, hide_main=False)
#         yield modname


def package_modpaths(pkgpath, with_pkg=False, with_mod=True, followlinks=True,
                     recursive=True):
    r"""
    Finds sub-packages and sub-modules belonging to a package.

    Args:
        pkgpath (str): path to a module or package
        with_pkg (bool): if True includes package __init__ files (default =
            False)
        with_mod (bool): if True includes module files (default = True)
        exclude (list): ignores any module that matches any of these patterns
        recursive (bool): if False, then only child modules are included

    Yields:
        str: module names belonging to the package

    References:
        http://stackoverflow.com/questions/1707709/list-modules-in-py-package

    Example:
        >>> from xdoctest.static_analysis import *
        >>> pkgpath = modname_to_modpath('xdoctest')
        >>> paths = list(package_modpaths(pkgpath))
        >>> names = list(map(modpath_to_modname, paths))
        >>> assert 'xdoctest.core' in names
        >>> assert 'xdoctest.__main__' in names
        >>> assert 'xdoctest' not in names
        >>> print('\n'.join(names))
    """
    if isfile(pkgpath):
        # If input is a file, just return it
        yield pkgpath
    else:
        if with_pkg:
            root_path = join(pkgpath, '__init__.py')
            if exists(root_path):
                yield root_path

        valid_exts = ['.py', _platform_pylib_ext()]
        for dpath, dnames, fnames in os.walk(pkgpath, followlinks=followlinks):
            ispkg = exists(join(dpath, '__init__.py'))
            if ispkg:
                if with_mod:
                    for fname in fnames:
                        if splitext(fname)[1] in valid_exts:
                            # dont yield inits. Handled in pkg loop.
                            if fname != '__init__.py':
                                path = join(dpath, fname)
                                yield path
                if with_pkg:
                    for dname in dnames:
                        path = join(dpath, dname, '__init__.py')
                        if exists(path):
                            yield path
            else:
                # Stop recursing when we are out of the package
                del dnames[:]
            if not recursive:
                break


def split_modpath(modpath):
    """
    Splits the modpath into the dir that must be in PYTHONPATH for the module
    to be imported and the modulepath relative to this directory.

    Args:
        modpath (str): module filepath

    Returns:
        str: directory

    Example:
        >>> from xdoctest import static_analysis
        >>> modpath = static_analysis.__file__
        >>> modpath = modpath.replace('.pyc', '.py')
        >>> dpath, rel_modpath = split_modpath(modpath)
        >>> assert join(dpath, rel_modpath) == modpath
        >>> assert rel_modpath == join('xdoctest', 'static_analysis.py')
    """
    modpath_ = abspath(expanduser(modpath))
    if not exists(modpath_):
        raise ValueError('modpath={} is not a module'.format(modpath))
    if isdir(modpath_) and not exists(join(modpath, '__init__.py')):
        # dirs without inits are not modules
        raise ValueError('modpath={} is not a module'.format(modpath))
    full_dpath, fname_ext = split(modpath_)
    _relmod_parts = [fname_ext]
    # Recurse down directories until we are out of the package
    dpath = full_dpath
    while exists(join(dpath, '__init__.py')):
        dpath, dname = split(dpath)
        _relmod_parts.append(dname)
    relmod_parts = _relmod_parts[::-1]
    rel_modpath = os.path.sep.join(relmod_parts)
    return dpath, rel_modpath


def modpath_to_modname(modpath, hide_init=True, hide_main=False):
    r"""
    Determines importable name from file path

    The filename is converted to a module name, and parent directories are
    recursively included until a directory without an __init__.py file is
    encountered.

    Args:
        modpath (str): module filepath

    Returns:
        str: modname

    Example:
        >>> from xdoctest import static_analysis
        >>> modpath = static_analysis.__file__
        >>> modpath = modpath.replace('.pyc', '.py')
        >>> modname = modpath_to_modname(modpath)
        >>> assert modname == 'xdoctest.static_analysis'
    """
    modpath_ = abspath(expanduser(modpath))
    dpath, rel_modpath = split_modpath(modpath_)
    modname = splitext(rel_modpath)[0]
    modname = modname.replace('/', '.')
    modname = modname.replace('\\', '.')
    if hide_init:
        if modname.endswith('.__init__'):
            modname = modname[:-len('.__init__')]
    else:
        # add in init, if reasonable
        if not modname.endswith('.__init__'):
            if exists(join(modpath_, '__init__.py')):
                modname = modname + '.__init__'

    if hide_main:
        modname = modname.replace('.__main__', '').strip()
    return modname


def modname_to_modpath(modname, hide_init=True, hide_main=False):
    r"""
    Determines the path to a python module without directly import it

    Args:
        modname (str): module filepath
        hide_init (bool): if False, __init__.py will be returned for packages
        hide_main (bool): if False, and hide_init is True, __main__.py will be
            returned for packages, if it exists.

    Returns:
        str: modpath

    CommandLine:
        python -m xdoctest.static_analysis modname_to_modpath:0
        pytest  /home/joncrall/code/xdoctest/xdoctest/static_analysis.py::modname_to_modpath:0

    Example:
        >>> modname = 'xdoctest.__main__'
        >>> modpath = modname_to_modpath(modname, hide_main=False)
        >>> assert modpath.endswith('__main__.py')
        >>> modname = 'xdoctest'
        >>> modpath = modname_to_modpath(modname, hide_init=False)
        >>> assert modpath.endswith('__init__.py')
    """
    modpath = _syspath_modname_to_modpath(modname)
    if modpath is None:
        return None
    if hide_init:
        if basename(modpath) == '__init__.py':
            modpath = dirname(modpath)
            hide_main = True
    else:
        modpath_with_init = join(modpath, '__init__.py')
        if exists(modpath_with_init):
            modpath = modpath_with_init
    if hide_main:
        # We can remove main, but dont add it
        if basename(modpath) == '__main__.py':
            # corner case where main might just be a module name not in a pkg
            parallel_init = join(dirname(modpath), '__init__.py')
            if exists(parallel_init):
                modpath = dirname(modpath)
    # else:
    #     modpath_with_main = join(modpath, '__main__.py')
    #     if exists(modpath_with_main):
    #         modpath = modpath_with_main
    return modpath


def _syspath_modname_to_modpath(modname):
    """
    syspath version of modname_to_modpath

    Note, this is much slower than the pkgutil mechanisms.

    Example:
        >>> modname = 'xdoctest.static_analysis'
    """

    def _isvalid(modpath, base):
        # every directory up to the module, should have an init
        subdir = dirname(modpath)
        while subdir and subdir != base:
            if not exists(join(subdir, '__init__.py')):
                return False
            subdir = dirname(subdir)
        return True

    from os.path import join, isfile, exists
    import sys
    _fname_we = modname.replace('.', os.path.sep)
    candidate_fnames = [
        _fname_we + '.py',
        # _fname_we + '.pyc',
        # _fname_we + '.pyo',
        _fname_we + _platform_pylib_ext()
    ]
    candidate_dpaths = ['.'] + sys.path
    for dpath in candidate_dpaths:
        # Check for directory-based modules (has presidence over files)
        modpath = join(dpath, _fname_we)
        if exists(modpath):
            if isfile(join(modpath, '__init__.py')):
                if _isvalid(modpath, dpath):
                    return modpath

        # If that fails, check for file-based modules
        for fname in candidate_fnames:
            modpath = join(dpath, fname)
            if isfile(modpath):
                if _isvalid(modpath, dpath):
                    return modpath


def is_balanced_statement(lines):
    """
    Checks if the lines have balanced parens, brakets, curlies and strings

    Args:
        lines (list): list of strings

    Returns:
        bool: False if the statement is not balanced

    Doctest:
        >>> assert is_balanced_statement(['print(foobar)'])
        >>> assert is_balanced_statement(['foo = bar']) is True
        >>> assert is_balanced_statement(['foo = (']) is False
        >>> assert is_balanced_statement(['foo = (', "')(')"]) is True
        >>> assert is_balanced_statement(
        ...     ['foo = (', "'''", ")]'''", ')']) is True
        >>> #assert is_balanced_statement(['foo = ']) is False
        >>> #assert is_balanced_statement(['== ']) is False

    """
    block = '\n'.join(lines)
    if six.PY2:
        block = block.encode('utf8')
    stream = StringIO()
    stream.write(block)
    stream.seek(0)
    try:
        for t in tokenize.generate_tokens(stream.readline):
            pass
    except tokenize.TokenError as ex:
        message = ex.args[0]
        if message.startswith('EOF in multi-line'):
            return False
        raise
    else:
        # Note: trying to use ast.parse(block) will not work
        # here because it breaks in try, except, else
        return True


if __name__ == '__main__':
    import xdoctest as xdoc
    xdoc.doctest_module()

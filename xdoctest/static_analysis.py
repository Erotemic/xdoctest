# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import ast
import re
import pkgutil
import tokenize
import six
from fnmatch import fnmatch
from six.moves import cStringIO as StringIO
from collections import deque
from os.path import (join, exists, expanduser, abspath, split, splitext,
                     isfile, dirname)

# CallDefNode = namedtuple('CallDefNode',
#                          ('callname', 'lineno', 'docstr', 'doclineno'))


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
        >>> import ubelt as ub
        >>> source = ub.codeblock(
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
        self.calldefs = {}
        self.sourcelines = None

        self._current_classname = None
        # Keep track of when we leave a top level definition
        self._finish_queue = deque()
        self._prev_pop = None

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
        source_utf8 = source.encode('utf8')
        pt = ast.parse(source_utf8)
        self = TopLevelVisitor()
        self.sourcelines = source.splitlines()
        self.visit(pt)
        lineno_end = source.count('\n') + 2  # one indexing
        self.process_finished(lineno_end)
        return self

    def visit(self, node):
        self.process_finished(node)
        super(TopLevelVisitor, self).visit(node)

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
                nlines = docnode.value.s.count('\n')
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

    # def visit_Assign(self, node):
    #     # print('VISIT FunctionDef node = %r' % (node,))
    #     # print('VISIT FunctionDef node = %r' % (node.__dict__,))
    #     # for target in node.targets:
    #     #     print('target.id = %r' % (target.id,))
    #     # print('node.value = %r' % (node.value,))
    #     # TODO: assign constants to
    #     # self.const_lookup
    #     self.generic_visit(node)

    def visit_If(self, node):
        if isinstance(node.test, ast.Compare):
            try:
                if all([
                    isinstance(node.test.ops[0], ast.Eq),
                    node.test.left.id == '__name__',
                    node.test.comparators[0].s == '__main__',
                ]):
                    # Ignore main block
                    return
            except Exception as ex:
                pass
        self.generic_visit(node)


def parse_calldefs(source=None, fpath=None):
    r"""
    Statically finds top-level callable functions and methods in python source

    Args:
        source (str): python text
        fpath (str): filepath to read if source is not specified

    Returns:
        dict(str, CallDefNode): map of callnames to tuples with def info

    CommandLine:
        python -m ubelt.meta.static_analysis parse_calldefs

    Example:
        >>> from ubelt.meta.static_analysis import *  # NOQA
        >>> import ubelt as ub
        >>> fpath = ub.meta.static_analysis.__file__.replace('.pyc', '.py')
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


def package_modnames(package_name, with_pkg=False, with_mod=True, exclude=[]):
    r"""
    Finds sub-packages and sub-modules belonging to a package.

    Args:
        package_name (str): package or module name
        with_pkg (bool): if True includes package directories with __init__
            files (default = False)
        with_mod (bool): if True includes module files (default = True)
        exclude (list): ignores any module that matches any of these patterns

    Yields:
        str: module names belonging to the package

    References:
        http://stackoverflow.com/questions/1707709/list-modules-in-py-package

    CommandLine:
        python -m ubelt.meta.static_analysis package_modnames

    Example:
        >>> from ubelt.meta.static_analysis import *  # NOQA
        >>> exclude = ['*util_*']
        >>> with_pkg, with_mod = False, True
        >>> names = list(package_modnames('ubelt', with_pkg, with_mod, exclude))
        >>> assert 'ubelt.meta' not in names
        >>> assert 'ubelt.meta.static_analysis' in names
        >>> #print('\n'.join(names))

    Example:
        >>> from ubelt.meta.static_analysis import *  # NOQA
        >>> with_pkg, with_mod = True, False
        >>> names = list(package_modnames('ubelt', with_pkg, with_mod))
        >>> assert 'ubelt.meta' in names
        >>> assert 'ubelt.meta.static_analysis' not in names
        >>> #print('\n'.join(names))
    """
    modpath = modname_to_modpath(package_name, hide_init=True)
    if isfile(modpath):
        # If input is a file, just return it
        yield package_name
    else:
        # Otherwise, if it is a package, find sub-packages and sub-modules
        prefix = package_name + '.'
        walker = pkgutil.walk_packages([modpath], prefix=prefix,
                                       onerror=lambda x: None)  # nocover
        for importer, modname, ispkg in walker:
            if any(fnmatch(modname, pat) for pat in exclude):
                continue
            elif not ispkg and with_mod:
                yield modname
            elif ispkg and with_pkg:
                yield modname


def modpath_to_modname(modpath):
    r"""
    Determines importable name from file path

    Args:
        modpath (str): module filepath

    Returns:
        str: modname

    Example:
        >>> from ubelt.meta.static_analysis import *  # NOQA
        >>> import ubelt.meta.static_analysis
        >>> modpath = ubelt.meta.static_analysis.__file__
        >>> modpath = modpath.replace('.pyc', '.py')
        >>> #print('modpath = %r' % (modpath))
        >>> modname = modpath_to_modname(modpath)
        >>> #print('modname = %r' % (modname,))
        >>> assert modname == 'ubelt.meta.static_analysis'
    """
    modpath_ = abspath(expanduser(modpath))
    full_dpath, fname_ext = split(modpath_)
    fname, ext = splitext(fname_ext)
    _modsubdir_list = [fname]
    # Recurse down directories until we are out of the package
    dpath = full_dpath
    while exists(join(dpath, '__init__.py')):
        dpath, dname = split(dpath)
        _modsubdir_list.append(dname)
    modsubdir_list = _modsubdir_list[::-1]
    modname = '.'.join(modsubdir_list)
    modname = modname.replace('.__init__', '').strip()
    modname = modname.replace('.__main__', '').strip()
    return modname


def modname_to_modpath(modname, hide_init=True, hide_main=True):
    r"""
    Determines the path to a python module without directly import it

    Args:
        modname (str): module filepath

    Returns:
        str: modpath

    CommandLine:
        python -m ubelt.meta.static_analysis modname_to_modpath

    TODO:
        Test with a module we know wont be imported by ubelt.
        Maybe make this a non-doctest and put in tests directory.

    Example:
        >>> from ubelt.meta.static_analysis import *  # NOQA
        >>> import sys
        >>> modname = 'ubelt.progiter'
        >>> already_exists = modname in sys.modules
        >>> modpath = modname_to_modpath(modname)
        >>> #print('modpath = %r' % (modpath,))
        >>> assert already_exists or modname not in sys.modules

    Example:
        >>> from ubelt.meta.static_analysis import *  # NOQA
        >>> import sys
        >>> modname = 'ubelt.__main__'
        >>> modpath = modname_to_modpath(modname, hide_main=False)
        >>> #print('modpath = %r' % (modpath,))
        >>> assert modpath.endswith('__main__.py')
        >>> modname = 'ubelt'
        >>> modpath = modname_to_modpath(modname, hide_init=False)
        >>> #print('modpath = %r' % (modpath,))
        >>> assert modpath.endswith('__init__.py')
        >>> modname = 'ubelt'
        >>> modpath = modname_to_modpath(modname, hide_init=False, hide_main=False)
        >>> #print('modpath = %r' % (modpath,))
        >>> assert modpath.endswith('__main__.py')
    """
    loader = pkgutil.find_loader(modname)
    if loader is None:
        raise Exception('No module named {} in the PYTHONPATH'.format(modname))
        # return None
    modpath = loader.get_filename().replace('.pyc', '.py')
    # if '.' not in basename(modpath):
    #     modpath = join(modpath, '__init__.py')
    if hide_init:
        if modpath.endswith(('__init__.py')):
            modpath = dirname(modpath)
    if not hide_main:
        if modpath.endswith('__init__.py'):
            main_modpath = modpath[:-len('__init__.py')] + '__main__.py'
            if exists(main_modpath):  # pragma: no branch
                modpath = main_modpath
    return modpath


def is_complete_statement(lines):
    """
    Checks if the lines form a complete python statment.
    Currently only handles balanced parans.

    Args:
        lines (list): list of strings

    Doctest:
        >>> from ubelt.meta.static_analysis import *  # NOQA
        >>> assert is_complete_statement(['print(foobar)'])
        >>> assert is_complete_statement(['foo = bar']) is True
        >>> assert is_complete_statement(['foo = (']) is False
        >>> assert is_complete_statement(['foo = (', "')(')"]) is True
        >>> assert is_complete_statement(
        ...     ['foo = (', "'''", ")]'''", ')']) is True
        >>> #assert is_complete_statement(['foo = ']) is False
        >>> #assert is_complete_statement(['== ']) is False

    """
    # import token
    if six.PY2:
        block = '\n'.join(lines).encode('utf8')
    else:
        block = '\n'.join(lines)
    stream = StringIO()
    stream.write(block)
    stream.seek(0)
    try:
        # tokens = []
        for t in tokenize.generate_tokens(stream.readline):
            # tok_type = token.tok_name[t[0]]
            # tokens.append((tok_type, t[1]))
            pass
    except tokenize.TokenError as ex:
        message = ex.args[0]
        if message.startswith('EOF in multi-line'):
            return False
        raise
    else:
        # FIXME: breaks on try: Except: else:
        # try:
        #     # Now check if forms a valid parse tree
        #     ast.parse(block)
        # except SyntaxError:
        #     return False
        return True

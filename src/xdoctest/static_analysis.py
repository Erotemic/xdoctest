"""
The core logic that allows for xdoctest to parse source statically
"""
import sys
from os.path import exists
from os.path import isfile
from os.path import join
from os.path import splitext
import os
import ast
import re
from collections import deque, OrderedDict
from xdoctest import utils

from xdoctest.utils.util_import import _platform_pylib_exts # NOQA
from xdoctest.utils.util_import import (  # NOQA
    split_modpath, modname_to_modpath, is_modname_importable,
    modpath_to_modname)

import platform
PLAT_IMPL = platform.python_implementation()


IS_PY_GE_312 = sys.version_info[0:2] >= (3, 12)
IS_PY_GE_308 = sys.version_info[0:2] >= (3, 8)  # type: bool
IS_PY_LT_314 = sys.version_info[0:2] < (3, 14)  # type: bool


if IS_PY_GE_312:
    from xdoctest import _tokenize as tokenize
else:
    import tokenize


class CallDefNode:
    """
    Attributes:
        lineno_end (None | int):
            the line number the docstring ends on (if known)
    """
    def __init__(self, callname, lineno, docstr, doclineno, doclineno_end,
                 args=None):
        """
        Args:
            callname (str):
                the name of the item containing the docstring.

            lineno (int):
                the line number the item containing the docstring.

            docstr (str):
                the docstring itself

            doclineno (int):
                the line number (1 based) the docstring begins on

            doclineno_end (int):
                the line number (1 based) the docstring ends on

            args (None | ast.arguments):
                arguments from static analysis :class:`TopLevelVisitor`.
        """
        self.callname = callname
        self.lineno = lineno
        self.docstr = docstr
        self.doclineno = doclineno
        self.doclineno_end = doclineno_end
        self.lineno_end = None
        self.args = args

    def __str__(self):
        """
        Returns:
            str
        """
        return '{}[{}:{}][{}]'.format(
            self.callname, self.lineno, self.lineno_end,
            self.doclineno)


class TopLevelVisitor(ast.NodeVisitor):
    """
    Parses top-level function names and docstrings

    For other ``visit_<classname>`` values see [MeetTheNodes]_.

    References:
        .. [MeetTheNodes] http://greentreesnakes.readthedocs.io/en/latest/nodes.html

    CommandLine:
        python -m xdoctest.static_analysis TopLevelVisitor

    Attributes:
        calldefs (OrderedDict):
        source (None | str):
        sourcelines (None | List[str]):
        assignments (list):

    Example:
        >>> from xdoctest.static_analysis import *  # NOQA
        >>> from xdoctest import utils
        >>> source = utils.codeblock(
                '''
                def foo():
                    \"\"\" my docstring \"\"\"
                    def subfunc():
                        pass
                def bar():
                    pass
                class Spam:
                    def eggs(self):
                        pass
                    @staticmethod
                    def hams():
                        pass
                    @property
                    def jams(self):
                        return 3
                    @jams.setter
                    def jams2(self, x):
                        print('ignoring')
                    @jams.deleter
                    def jams(self, x):
                        print('ignoring')
                ''')
        >>> self = TopLevelVisitor.parse(source)
        >>> callnames = set(self.calldefs.keys())
        >>> assert callnames == {
        >>>     'foo', 'bar', 'Spam', 'Spam.eggs', 'Spam.hams',
        >>>     'Spam.jams'}
        >>> assert self.calldefs['foo'].docstr.strip() == 'my docstring'
        >>> assert 'subfunc' not in self.calldefs
    """
    @classmethod
    def parse(cls, source):
        """
        main entry point

        executes parsing algorithm and populates self.calldefs

        Args:
            source (str):
        """
        self = cls(source)
        pt = self.syntax_tree()

        self.visit(pt)

        lineno_end = source.count('\n') + 2  # one indexing
        self.process_finished(lineno_end)
        return self

    def __init__(self, source=None):
        """
        Args:
            source (None | str):
        """
        super(TopLevelVisitor, self).__init__()
        self.calldefs = OrderedDict()
        self.source = source
        self.sourcelines = None

        self._current_classname = None
        # Keep track of when we leave a top level definition
        self._finish_queue = deque()

        # new
        self.assignments = []

    def syntax_tree(self):
        """
        creates the abstract syntax tree

        Returns:
            ast.Module:
        """
        self.sourcelines = self.source.splitlines()
        source_utf8  = self.source.encode('utf8')
        pt = ast.parse(source_utf8)
        return pt

    def process_finished(self, node):
        """
        process (get ending lineno) for everything marked as finished

        Args:
            node (ast.AST):
        """
        if self._finish_queue:
            if isinstance(node, int):
                lineno_end = node
            else:
                lineno_end = getattr(node, 'lineno', None)
            while self._finish_queue:
                calldef = self._finish_queue.pop()
                calldef.lineno_end = lineno_end

    def visit(self, node):
        """
        Args:
            node (ast.AST):
        """
        self.process_finished(node)
        super(TopLevelVisitor, self).visit(node)

    def visit_FunctionDef(self, node):
        """
        Args:
            node (ast.FunctionDef):
        """
        if self._current_classname is None:
            callname = node.name
        else:
            callname = self._current_classname + '.' + node.name

        if node.decorator_list:
            for decor in node.decorator_list:
                if isinstance(decor, ast.Name):
                    if decor.id == 'property':
                        # likely a getter property
                        # should we distinguish getters?
                        # callname = callname + '.fget'
                        pass
                if isinstance(decor, ast.Attribute):
                    # Don't add setters / deleters to the callnames
                    if decor.attr == 'deleter':
                        # callname = callname + '.fdel'
                        return
                    if decor.attr == 'setter':
                        # callname = callname + '.fset'
                        return

        # TODO: Is this still necessary in modern Python versions?
        lineno = self._workaround_func_lineno(node)
        docstr, doclineno, doclineno_end = self._get_docstring(node)
        calldef = CallDefNode(callname, lineno, docstr, doclineno,
                              doclineno_end, args=node.args)
        self.calldefs[callname] = calldef

        self._finish_queue.append(calldef)

    def visit_ClassDef(self, node):
        """
        Args:
            node (ast.ClassDef):
        """
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
        """
        Args:
            node (ast.Module):
        """
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
        """
        Args:
            node (ast.Assign):
        """
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
        """
        Args:
            node (ast.If):
        """
        if isinstance(node.test, ast.Compare):  # pragma: nobranch
            try:
                if IS_PY_GE_312:
                    if all([
                        isinstance(node.test.ops[0], ast.Eq),
                        node.test.left.id == '__name__',
                        node.test.comparators[0].value == '__main__',
                    ]):
                        # Ignore main block
                        return
                else:
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

    def _docnode_line_workaround(self, docnode):
        """
        Find the start and ending line numbers of a docstring

        Args:
            docnode (ast.AST):

        Returns:
            Tuple[int, int]

        CommandLine:
            xdoctest -m xdoctest.static_analysis TopLevelVisitor._docnode_line_workaround

        Example:
            >>> from xdoctest.static_analysis import *  # NOQA
            >>> sq = chr(39)  # single quote
            >>> dq = chr(34)  # double quote
            >>> source = utils.codeblock(
                '''
                def func0():
                    {ddd} docstr0 {ddd}
                def func1():
                    {ddd}
                    docstr1 {ddd}
                def func2():
                    {ddd} docstr2
                    {ddd}
                def func3():
                    {ddd}
                    docstr3
                    {ddd}  # foobar
                def func5():
                    {ddd}pathological case
                    {sss} # {ddd} # {sss} # {ddd} # {ddd}
                def func6():
                    " single quoted docstr "
                def func7():
                    r{ddd}
                    raw line
                    {ddd}
                ''').format(ddd=dq * 3, sss=sq * 3)
            >>> self = TopLevelVisitor(source)
            >>> func_nodes = self.syntax_tree().body
            >>> print(utils.add_line_numbers(utils.highlight_code(source), start=1))
            >>> wants = [
            >>>     (2, 2),
            >>>     (4, 5),
            >>>     (7, 8),
            >>>     (10, 12),
            >>>     (14, 15),
            >>>     (17, 17),
            >>>     (19, 21),
            >>> ]
            >>> for i, func_node in enumerate(func_nodes):
            >>>     docnode = func_node.body[0]
            >>>     got = self._docnode_line_workaround(docnode)
            >>>     want = wants[i]
            >>>     print('got = {!r}'.format(got))
            >>>     print('want = {!r}'.format(want))
            >>>     assert got == want
        """
        # lineno points to the last line of a string in CPython < 3.8
        if hasattr(docnode, 'end_lineno'):
            endpos = docnode.end_lineno - 1
        else:
            if PLAT_IMPL == 'PyPy':
                startpos = docnode.lineno - 1
                if IS_PY_GE_312:
                    docstr = utils.ensure_unicode(docnode.value.value)
                else:
                    docstr = utils.ensure_unicode(docnode.value.s)
                sourcelines = self.sourcelines
                start, stop = self._find_docstr_endpos_workaround(docstr,
                                                                  sourcelines,
                                                                  startpos)
                # Convert 0-based line positions to 1-based line numbers
                doclineno = start + 1
                doclineno_end = stop + 1
                return doclineno, doclineno_end
            else:
                # Hack for older versions
                # TODO: fix in pypy
                endpos = docnode.lineno - 1

        if IS_PY_GE_312:
            docstr = utils.ensure_unicode(docnode.value.value)
        else:
            docstr = utils.ensure_unicode(docnode.value.s)
        sourcelines = self.sourcelines
        start, stop = self._find_docstr_startpos_workaround(docstr, sourcelines, endpos)
        # Convert 0-based line positions to 1-based line numbers
        doclineno = start + 1
        doclineno_end = stop
        # print('docnode = {!r}'.format(docnode))
        return doclineno, doclineno_end

    @classmethod
    def _find_docstr_endpos_workaround(cls, docstr, sourcelines, startpos):
        """
        Like docstr_line_workaround, but works from the top-down instead of
        bottom-up. This is for pypy.


        Given a docstring, its original source lines, and where the start
        position is, this function finds the end-position of the docstr

        Example:
            >>> fmtkw = dict(sss=chr(39) * 3, ddd=chr(34) * 3)
            >>> source = utils.codeblock(
                    '''
                    {ddd}
                    docstr0
                    {ddd}
                    '''.format(**fmtkw))
            >>> sourcelines = source.splitlines()
            >>> docstr = eval(source, {}, {})
            >>> startpos = 0
            >>> start, stop = TopLevelVisitor._find_docstr_endpos_workaround(docstr, sourcelines, startpos)
            >>> assert (start, stop) == (0, 2)
            >>> #
            >>> source = utils.codeblock(
                    '''
                    "docstr0"
                    '''.format(**fmtkw))
            >>> sourcelines = source.splitlines()
            >>> docstr = eval(source, {}, {})
            >>> startpos = 0
            >>> start, stop = TopLevelVisitor._find_docstr_endpos_workaround(docstr, sourcelines, startpos)
            >>> assert (start, stop) == (0, 0)
        """
        start = startpos
        stop = startpos
        startline = sourcelines[start]

        trips = ("'''", '"""')
        for trip in trips:
            if startline.strip().startswith((trip, 'r' + trip)):
                nlines = docstr.count('\n')
                # assuming that the docstr is actually terminated with this
                # kind of triple quote, then the end line is at this position
                cand_stop_ = start + nlines
                endline = sourcelines[cand_stop_]

                endpat = re.escape(trip) + r'\s*#.*$'
                endline_ = re.sub(endpat, trip, endline).strip()

                # The startline should also begin with the same triple quote
                # Account for raw strings. Note f-strings cannot be docstrings
                if endline_.endswith(trip):
                    stop = cand_stop_
                    break
                else:
                    # Conditions failed, revert to assuming a one-line string.
                    stop = start
        return start, stop

    def _find_docstr_startpos_workaround(self, docstr, sourcelines, endpos):
        r"""
        Find the which sourcelines contain the docstring

        Args:
            docstr (str): the extracted docstring.

            sourcelines (list): a list of all lines in the file. We assume
                the docstring exists as a pure string literal in the source.
                In other words, no postprocessing via split, format, or any
                other dynamic programmatic modification should be made to the
                docstrings. Python's docstring extractor assumes this as well.

            endpos (int): line position (starting at 0) the docstring ends on.
                Note: positions are 0 based but linenos are 1 based.

        Returns:
            tuple[Int, Int]: start, stop:
                start: the line position (0 based) the docstring starts on
                stop: the line position (0 based) that the docstring stops

                such that sourcelines[start:stop] will contain the docstring

        CommandLine:
            python -m xdoctest xdoctest.static_analysis TopLevelVisitor._find_docstr_startpos_workaround
            python -m xdoctest xdoctest.static_analysis TopLevelVisitor._find_docstr_startpos_workaround --debug

        Example:
            >>> # xdoctest: +REQUIRES(CPython)
            >>> # This function is a specific workaround for a CPython bug.
            >>> from xdoctest.static_analysis import *
            >>> sq = chr(39)  # single quote
            >>> dq = chr(34)  # double quote
            >>> source = utils.codeblock(
                '''
                def func0():
                    {ddd} docstr0 {ddd}
                def func1():
                    {ddd}
                    docstr1 {ddd}
                def func2():
                    {ddd} docstr2
                    {ddd}
                def func3():
                    {ddd}
                    docstr3
                    {ddd}  # foobar
                def func5():
                    {ddd}pathological case
                    {sss} # {ddd} # {sss} # {ddd} # {ddd}
                def func6():
                    " single quoted docstr "
                def func7():
                    r{ddd}
                    raw line
                    {ddd}
                ''').format(ddd=dq * 3, sss=sq * 3)
            >>> print(utils.add_line_numbers(utils.highlight_code(source), start=0))
            >>> targets = [
            >>>     (1, 2),
            >>>     (3, 5),
            >>>     (6, 8),
            >>>     (9, 12),
            >>>     (13, 15),
            >>>     (16, 17),
            >>>     (18, 21),
            >>> ]
            >>> self = TopLevelVisitor.parse(source)
            >>> pt = ast.parse(source.encode('utf8'))
            >>> sourcelines = source.splitlines()
            >>> # PYPY docnode.lineno specify the startpos of a docstring not
            >>> # the end.
            >>> print('\n\n====\n\n')
            >>> #for i in [0, 1]:
            >>> for i in range(len(targets)):
            >>>     print('----------')
            >>>     funcnode = pt.body[i]
            >>>     print('funcnode = {!r}'.format(funcnode))
            >>>     docnode = funcnode.body[0]
            >>>     print('funcnode.__dict__ = {!r}'.format(funcnode.__dict__))
            >>>     print('docnode = {!r}'.format(docnode))
            >>>     print('docnode.value = {!r}'.format(docnode.value))
            >>>     print('docnode.value.__dict__ = {!r}'.format(docnode.value.__dict__))
            >>>     if IS_PY_GE_312:
            >>>         print('docnode.value.value = {!r}'.format(docnode.value.value))
            >>>     else:
            >>>         print('docnode.value.s = {!r}'.format(docnode.value.s))
            >>>     print('docnode.lineno = {!r}'.format(docnode.lineno))
            >>>     print('docnode.col_offset = {!r}'.format(docnode.col_offset))
            >>>     print('docnode = {!r}'.format(docnode))
            >>>     #import IPython
            >>>     #IPython.embed()
            >>>     docstr = ast.get_docstring(funcnode, clean=False)
            >>>     print('len(docstr) = {}'.format(len(docstr)))
            >>>     endpos = docnode.lineno - 1
            >>>     if hasattr(docnode, 'end_lineno'):
            >>>         endpos = docnode.end_lineno - 1
            >>>     print('endpos = {!r}'.format(endpos))
            >>>     start, end = self._find_docstr_startpos_workaround(docstr, sourcelines, endpos)
            >>>     print('i = {!r}'.format(i))
            >>>     print('got  = {}, {}'.format(start, end))
            >>>     print('want = {}, {}'.format(*targets[i]))
            >>>     if targets[i] != (start, end):
            >>>         print('---')
            >>>         print(docstr)
            >>>         print('---')
            >>>         print('sourcelines = [\n{}\n]'.format(', \n'.join(list(map(repr, enumerate(sourcelines))))))
            >>>         print('endpos = {!r}'.format(endpos))
            >>>         raise AssertionError('docstr workaround is failing')
            >>>     print('----------')
        """
        # First assume a one-line string that starts and stops on the same line
        start = endpos
        stop = endpos + 1
        endline = sourcelines[stop - 1]

        # Determine if the docstring is a triple quoted string, by trying both
        # triple quote styles and checking if the string starts and ends with
        # the same style. If both cases are true we know we are in a triple
        # quoted string literal and can therefore safely extract the starting
        # line position.
        trips = ("'''", '"""')
        for trip in trips:
            pattern = re.escape(trip) + r'\s*#.*$'
            # Assuming the multiline string is using `trip` as the triple quote
            # format, then the first instance of that pattern must terminate
            # the string literal. Afterwards the only valid characters are
            # whitespace and comments. Anything after the comment can be
            # ignored. The above pattern will match the first triple quote it
            # sees, and then will remove any trailing comments.
            endline_ = re.sub(pattern, trip, endline).strip()
            # After removing comments, if the endline endswith a triple quote,
            # then we must be in a multiline string IF the startline starts
            # with that same triple quote. We should be able to determine where
            # the startline is because we know how many newline characters are
            # in the extracted docstring. This works because all newline
            # characters in multiline string literals MUST correspond to actual
            # newlines in the source code.
            if endline_.endswith(trip):
                nlines = docstr.count('\n')
                # assuming that the docstr is actually terminated with this
                # kind of triple quote, then the start line is at this position
                cand_start_ = stop - nlines - 1
                startline = sourcelines[cand_start_]

                # The startline should also begin with the same triple quote
                # Account for raw strings. Note f-strings cannot be docstrings
                if startline.strip().startswith((trip, 'r' + trip)):
                    # Both conditions pass.
                    start = cand_start_
                    break
                else:
                    # Conditions failed, revert to assuming a one-line string.
                    start = stop - 1
        return start, stop

    def _get_docstring(self, node):
        """
        CommandLine:
            xdoctest -m xdoctest.static_analysis.py TopLevelVisitor._get_docstring

        Example:
            >>> source = utils.codeblock(
                '''
                def foo():
                    'docstr'
                ''')
            >>> self = TopLevelVisitor(source)
            >>> node = self.syntax_tree().body[0]
            >>> self._get_docstring(node)
            ('docstr', 2, 2)
        """
        docstr = ast.get_docstring(node, clean=False)
        if docstr is not None:
            docnode = node.body[0]
            doclineno, doclineno_end = self._docnode_line_workaround(docnode)
        else:
            doclineno = None
            doclineno_end = None
        return (docstr, doclineno, doclineno_end)

    def _workaround_func_lineno(self, node):
        """
        Finds the correct line for the original function definition even when
        decorators are involved.

        Example:
            >>> source = utils.codeblock(
                '''
                @bar
                @baz
                def foo():
                    'docstr'
                ''')
            >>> self = TopLevelVisitor(source)
            >>> node = self.syntax_tree().body[0]
            >>> self._workaround_func_lineno(node)
            3
        """
        # Try and find the lineno of the function definition
        # (maybe the fact that its on a decorator is actually right...)
        if node.decorator_list:
            # Decorators can throw off the line the function is declared on
            linex = node.lineno - 1
            pattern = r'\s*def\s*' + node.name
            # I think this is actually robust
            while not re.match(pattern, self.sourcelines[linex]):
                linex += 1
            lineno = linex + 1
        else:
            lineno = node.lineno
        return lineno


def parse_static_calldefs(source=None, fpath=None):
    """
    Statically finds top-level callable functions and methods in python source

    Args:
        source (str): python text
        fpath (str): filepath to read if source is not specified

    Returns:
        Dict[str, CallDefNode]:
            mapping from callnames to CallDefNodes, which contain
               info about the item with the doctest.

    Example:
        >>> from xdoctest import static_analysis
        >>> fpath = static_analysis.__file__.replace('.pyc', '.py')
        >>> calldefs = parse_static_calldefs(fpath=fpath)
        >>> assert 'parse_static_calldefs' in calldefs
    """
    if source is None:  # pragma: no branch
        try:
            with open(fpath, 'rb') as file_:
                source = file_.read().decode('utf-8')
        except Exception:
            try:
                with open(fpath, 'rb') as file_:
                    source = file_.read()
            except Exception:
                print('Unable to read fpath = {!r}'.format(fpath))
                raise
    try:
        self = TopLevelVisitor.parse(source)
        return self.calldefs
    except Exception:  # nocover
        if fpath:
            print('Failed to parse docstring for fpath=%r' % (fpath,))
        else:
            print('Failed to parse docstring')
        raise


def parse_calldefs(source=None, fpath=None):
    from xdoctest.utils import util_deprecation
    util_deprecation.schedule_deprecation(
        modname='xdoctest',
        name='parse_calldefs', type='function',
        migration='use parse_static_calldefs instead',
        deprecate='1.0.0', error='1.1.0', remove='1.2.0'
    )
    return parse_static_calldefs(source=source, fpath=fpath)


def _parse_static_node_value(node):
    """
    Extract a constant value from a node if possible
    """
    import numbers
    if (isinstance(node, ast.Constant) and isinstance(node.value, numbers.Number)):
        value = node.value
    elif (isinstance(node, ast.Constant) and isinstance(node.value, str)):
        value = node.value
    elif isinstance(node, ast.List):
        value = list(map(_parse_static_node_value, node.elts))
    elif isinstance(node, ast.Tuple):
        value = tuple(map(_parse_static_node_value, node.elts))
    elif isinstance(node, (ast.Dict)):
        keys = map(_parse_static_node_value, node.keys)
        values = map(_parse_static_node_value, node.values)
        value = OrderedDict(zip(keys, values))
        # value = dict(zip(keys, values))
    elif IS_PY_LT_314 and isinstance(node, (ast.NameConstant)):
        value = node.value
    elif isinstance(node, ast.Constant):
        value = node.value
    else:
        print(node.__dict__)
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

    Returns:
        object

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
        >>> source = 'foo = None'
        >>> assert parse_static_value(key, source=source) == None
        >>> #parse_static_value('bar', source=source)
        >>> #parse_static_value('bar', source='foo=1; bar = [1, foo]')
    """
    if source is None:  # pragma: no branch
        try:
            with open(fpath, 'rb') as file_:
                source = file_.read().decode('utf-8')
        except Exception:
            with open(fpath, 'rb') as file_:
                source = file_.read()
    pt = ast.parse(source)

    class AssignentVisitor(ast.NodeVisitor):
        def visit_Assign(self, node):
            for target in node.targets:
                target_id = getattr(target, 'id', None)
                if target_id == key:
                    self.value = _parse_static_node_value(node.value)

    sentinel = object()
    visitor = AssignentVisitor()
    visitor.value = sentinel
    visitor.visit(pt)
    if visitor.value is sentinel:
        raise NameError('No static variable named {!r}'.format(key))
    return visitor.value


def package_modpaths(pkgpath, with_pkg=False, with_mod=True, followlinks=True,
                     recursive=True, with_libs=False, check=True):
    r"""
    Finds sub-packages and sub-modules belonging to a package.

    Args:
        pkgpath (str): path to a module or package
        with_pkg (bool): if True includes package __init__ files (default =
            False)
        with_mod (bool): if True includes module files (default = True)
        exclude (list): ignores any module that matches any of these patterns
        recursive (bool): if False, then only child modules are included
        with_libs (bool): if True then compiled shared libs will be returned as well
        check (bool): if False, then then pkgpath is considered a module even
            if it does not contain an __init__ file.

    Yields:
        str: module names belonging to the package

    References:
        http://stackoverflow.com/questions/1707709/list-modules-in-py-package

    Example:
        >>> from xdoctest.static_analysis import *
        >>> pkgpath = modname_to_modpath('xdoctest')
        >>> paths = list(package_modpaths(pkgpath))
        >>> print('\n'.join(paths))
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
            if not check or exists(root_path):
                yield root_path

        valid_exts = ['.py']
        if with_libs:
            valid_exts += utils.util_import._platform_pylib_exts()

        for dpath, dnames, fnames in os.walk(pkgpath, followlinks=followlinks):
            ispkg = exists(join(dpath, '__init__.py'))
            if ispkg or not check:
                check = True  # always check subdirs
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


def is_balanced_statement(lines, only_tokens=False, reraise=0):
    r"""
    Checks if the lines have balanced braces and quotes.

    Args:
        lines (List[str]): list of strings, one for each line

    Returns:
        bool: True if the statement is balanced, otherwise False

    CommandLine:
        xdoctest -m xdoctest.static_analysis is_balanced_statement:0

    References:
        https://stackoverflow.com/questions/46061949/parse-until-complete

    Example:
        >>> from xdoctest.static_analysis import *  # NOQA
        >>> assert is_balanced_statement(['print(foobar)'])
        >>> assert is_balanced_statement(['foo = bar']) is True
        >>> assert is_balanced_statement(['foo = (']) is False
        >>> assert is_balanced_statement(['foo = (', "')(')"]) is True
        >>> assert is_balanced_statement(
        ...     ['foo = (', "'''", ")]'''", ')']) is True
        >>> assert is_balanced_statement(
        ...     ['foo = ', "'''", ")]'''", ')']) is False
        >>> #assert is_balanced_statement(['foo = ']) is False
        >>> #assert is_balanced_statement(['== ']) is False
        >>> lines = ['def foo():', '', '    x = 1', 'assert True', '']
        >>> assert is_balanced_statement(lines)

    Example:
        >>> from xdoctest.static_analysis import *
        >>> source_parts = [
        >>>     'setup(',
        >>>     "    name='extension',",
        >>>     '    ext_modules=[',
        >>>     '        CppExtension(',
        >>>     "            name='extension',",
        >>>     "            sources=['extension.cpp'],",
        >>>     "            extra_compile_args=['-g'])),",
        >>>     '    ],',
        >>> ]
        >>> print('\n'.join(source_parts))
        >>> assert not is_balanced_statement(source_parts)
        >>> source_parts = [
        >>>     'setup(',
        >>>     "    name='extension',",
        >>>     '    ext_modules=[',
        >>>     '        CppExtension(',
        >>>     "            name='extension',",
        >>>     "            sources=['extension.cpp'],",
        >>>     "            extra_compile_args=['-g']),",
        >>>     '    ],',
        >>>     '        cmdclass={',
        >>>     "            'build_ext': BuildExtension",
        >>>     '        })',
        >>> ]
        >>> print('\n'.join(source_parts))
        >>> assert is_balanced_statement(source_parts)

    Example:
        >>> lines = ['try: raise Exception']
        >>> is_balanced_statement(lines, only_tokens=1)
        True
        >>> is_balanced_statement(lines, only_tokens=0)
        False

    Example:
        >>> # Cause a failure case on 3.12
        >>> from xdoctest.static_analysis import *
        >>> lines = ['3, 4]', 'print(len(x))']
        >>> is_balanced_statement(lines, only_tokens=1)
        False
    """
    # Only iterate through non-empty lines otherwise tokenize will stop short
    lines = list(lines)
    iterable = (line for line in lines if line)
    def _readline():
        return next(iterable)
    try:
        for t in tokenize.generate_tokens(_readline):
            pass
    except tokenize.TokenError as ex:
        message = ex.args[0]
        # First case is Python <= 3.11, Second case is >= 3.12
        if message.startswith(('EOF in multi-line', 'unexpected EOF in multi-line')):
            if reraise:
                raise
            return False
        raise
    except IndentationError as ex:
        message = ex.args[0]
        if message.startswith('unindent does not match any outer indentation'):
            if reraise:
                raise
            return False
        raise
    else:
        # Note: trying to use ast.parse(block) will not work
        # here because it breaks in try, except, else
        if not only_tokens:
            # The above test wont trigger for cases involving higher level
            # python grammar. If we wish to test for these we will have to use
            # an AST.
            try:
                text = '\n'.join(lines)
                # from textwrap import dedent
                # text = dedent(text)
                six_axt_parse(text)
            except SyntaxError:
                if reraise:
                    raise
                return False
        return True


def extract_comments(source):
    """
    Returns the text in each comment in a block of python code.
    Uses tokenize to account for quotations.

    Args:
        source (str | List[str]):

    CommandLine:
        python -m xdoctest.static_analysis extract_comments

    Example:
        >>> from xdoctest import utils
        >>> source = utils.codeblock(
        >>>    '''
               # comment 1
               a = '# not a comment'  # comment 2
               c = 3
               ''')
        >>> comments = list(extract_comments(source))
        >>> assert comments == ['# comment 1', '# comment 2']
        >>> comments = list(extract_comments(source.splitlines()))
        >>> assert comments == ['# comment 1', '# comment 2']
    """
    if isinstance(source, str):
        lines = source.splitlines()
    else:
        lines = source

    # Only iterate through non-empty lines otherwise tokenize will stop short
    iterable = (line for line in lines if line)
    def _readline():
        return next(iterable)
    try:
        for t in tokenize.generate_tokens(_readline):
            if t[0] == tokenize.COMMENT:
                yield t[1]
    except tokenize.TokenError:
        pass


def _strip_hashtag_comments_and_newlines(source):
    """
    Removes hashtag comments from underlying source

    Args:
        source (str | List[str]):

    CommandLine:
        xdoctest -m xdoctest.static_analysis _strip_hashtag_comments_and_newlines

    TODO:
        would be better if this was some sort of configurable minify API

    Example:
        >>> from xdoctest.static_analysis import _strip_hashtag_comments_and_newlines
        >>> from xdoctest import utils
        >>> fmtkw = dict(sss=chr(39) * 3, ddd=chr(34) * 3)
        >>> source = utils.codeblock(
        >>>    '''
               # comment 1
               a = '# not a comment'  # comment 2

               multiline_string = {ddd}

               one

               {ddd}
               b = [
                   1,  # foo


                   # bar
                   3,
               ]
               c = 3
               ''').format(**fmtkw)
        >>> non_comments = _strip_hashtag_comments_and_newlines(source)
        >>> print(non_comments)
        >>> assert non_comments.count(chr(10)) == 10
        >>> assert non_comments.count('#') == 1
    """
    if isinstance(source, str):
        import io
        f = io.StringIO(source)
        readline = f.readline
    else:
        readline = iter(source).__next__

    def strip_hashtag_comments(tokens):
        """
        Drop comment tokens from a `tokenize` stream.
        """
        return (t for t in tokens if t[0] != tokenize.COMMENT)

    def strip_consecutive_newlines(tokens):
        """
        Consecutive newlines are dropped and trailing whitespace

        Adapted from: https://github.com/mitogen-hq/mitogen/blob/master/mitogen/minify.py#L65
        """
        prev_typ = None
        prev_end_col = 0
        skipped_rows = 0
        for token_info in tokens:
            typ, tok, (start_row, start_col), (end_row, end_col), line = token_info
            if typ in (tokenize.NL, tokenize.NEWLINE):
                if prev_typ in (tokenize.NL, tokenize.NEWLINE, None):
                    skipped_rows += 1
                    continue
                else:
                    start_col = prev_end_col
                end_col = start_col + 1
            prev_typ = typ
            prev_end_col = end_col
            yield typ, tok, (start_row - skipped_rows, start_col), (end_row - skipped_rows, end_col), line

    tokens = tokenize.generate_tokens(readline)
    tokens = strip_hashtag_comments(tokens)
    tokens = strip_consecutive_newlines(tokens)
    new_source = tokenize.untokenize(tokens)
    return new_source


def six_axt_parse(source_block, filename='<source_block>', compatible=True):
    """
    Python 2/3 compatible replacement for ast.parse(source_block, filename='<source_block>')

    Args:
        source (str):
        filename (str):
        compatible (bool):

    Returns:
        ast.Module | types.CodeType
    """
    pt = ast.parse(source_block, filename=filename)
    return pt


if __name__ == '__main__':
    import xdoctest as xdoc
    xdoc.doctest_module()

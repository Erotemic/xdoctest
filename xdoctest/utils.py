# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import six
# import codecs
import textwrap
from io import StringIO
# from six.moves import cStringIO as StringIO


def ensure_unicode(text):
    r"""
    Casts bytes into utf8 (mostly for python2 compatibility)

    References:
        http://stackoverflow.com/questions/12561063/python-extract-data-from-file

    Example:
        >>> from xdoctest.utils import *
        >>> assert ensure_unicode('my ünicôdé strįng') == 'my ünicôdé strįng'
        >>> assert ensure_unicode('text1') == 'text1'
        >>> assert ensure_unicode('text1'.encode('utf8')) == 'text1'
        >>> assert ensure_unicode('ï»¿text1'.encode('utf8')) == 'ï»¿text1'
        >>> import codecs
        >>> assert (codecs.BOM_UTF8 + 'text»¿'.encode('utf8')).decode('utf8')
    """
    if isinstance(text, six.text_type):
        return text
    elif isinstance(text, six.binary_type):
        return text.decode('utf8')
    else:  # nocover
        raise ValueError('unknown input type {!r}'.format(text))


class TeeStringIO(StringIO):
    """ simple class to write to a stdout and a StringIO """
    def __init__(self, redirect=None):
        self.redirect = redirect
        super(TeeStringIO, self).__init__()

    def write(self, msg):
        if self.redirect is not None:
            self.redirect.write(msg)
        if six.PY2:
            msg = ensure_unicode(msg)
        super(TeeStringIO, self).write(msg)

    def flush(self):  # nocover
        if self.redirect is not None:
            self.redirect.flush()
        super(TeeStringIO, self).flush()


class CaptureStdout(object):
    r"""
    Context manager that captures stdout and stores it in an internal stream

    Args:
        enabled (bool): (default = True)

    Example:
        >>> from xdoctest.utils import *
        >>> self = CaptureStdout(supress=True)
        >>> print('dont capture the table flip (╯°□°）╯︵ ┻━┻')
        >>> with self:
        ...     text = 'capture the heart ♥'
        ...     print(text)
        >>> print('dont capture look of disapproval ಠ_ಠ')
        >>> assert isinstance(self.text, six.text_type)
        >>> assert self.text == text + '\n', 'failed capture text'
    """
    def __init__(self, supress=True):
        self.supress = supress
        self.orig_stdout = sys.stdout
        if supress:
            redirect = None
        else:
            redirect = self.orig_stdout
        self.cap_stdout = TeeStringIO(redirect)
        # not needed when not using cStriongIO
        # if six.PY2:
        #     # http://stackoverflow.com/questions/1817695/stringio-accept-utf8
        #     codecinfo = codecs.lookup('utf8')
        #     self.cap_stdout = codecs.StreamReaderWriter(
        #         self.cap_stdout, codecinfo.streamreader,
        #         codecinfo.streamwriter)
        self.text = None

    def __enter__(self):
        sys.stdout = self.cap_stdout
        return self

    def __exit__(self, type_, value, trace):
        try:
            self.cap_stdout.seek(0)
            self.text = self.cap_stdout.read()
            # if six.PY2:  # nocover
            #     self.text = self.text.decode('utf8')
        except Exception:  # nocover
            raise
        finally:
            self.cap_stdout.close()
            sys.stdout = self.orig_stdout
        if trace is not None:
            return False  # return a falsey value on error


def indent(text, prefix='    '):
    r"""
    Indents a block of text

    Args:
        text (str): text to indent
        prefix (str): prefix to add to each line (default = '    ')

    Returns:
        str: indented text

    CommandLine:
        python -m util_str indent

    Example:
        >>> text = 'Lorem ipsum\ndolor sit amet'
        >>> prefix = '    '
        >>> result = indent(text, prefix)
        >>> assert all(t.startswith(prefix) for t in result.split('\n'))
    """
    return prefix + text.replace('\n', '\n' + prefix)


def highlight_code(text, lexer_name='python', **kwargs):
    r"""
    Highlights a block of text using ansii tags based on language syntax.

    Args:
        text (str): plain text to highlight
        lexer_name (str): name of language
        **kwargs: passed to pygments.lexers.get_lexer_by_name

    Returns:
        str: text : highlighted text
            If pygments is not installed, the plain text is returned.

    CommandLine:
        python -c "import pygments.formatters; print(list(pygments.formatters.get_all_formatters()))"

    Example:
        >>> text = 'import xdoctest as xdoc; print(xdoc)'
        >>> new_text = highlight_code(text)
        >>> print(new_text)
    """
    # Resolve extensions to languages
    lexer_name = {
        'py': 'python',
        'h': 'cpp',
        'cpp': 'cpp',
        'cxx': 'cpp',
        'c': 'cpp',
    }.get(lexer_name.replace('.', ''), lexer_name)
    try:
        import pygments
        import pygments.lexers
        import pygments.formatters
        import pygments.formatters.terminal
        formater = pygments.formatters.terminal.TerminalFormatter(bg='dark')
        lexer = pygments.lexers.get_lexer_by_name(lexer_name, ensurenl=False, **kwargs)
        new_text = pygments.highlight(text, lexer, formater)
    except ImportError:  # nocover
        import warnings
        warnings.warn('pygments is not installed')
        new_text = text
    return new_text


def codeblock(block_str):
    r"""
    Wraps multiline string blocks and returns unindented code.
    Useful for templated code defined in indented parts of code.

    Args:
        block_str (str): typically in the form of a multiline string

    Returns:
        str: the unindented string

    Example:
        >>> # Simulate an indented part of code
        >>> if True:
        ...     # notice the indentation on this will be normal
        ...     codeblock_version = codeblock(
        ...             '''
        ...             def foo():
        ...                 return 'bar'
        ...             '''
        ...         )
        ...     # notice the indentation and newlines on this will be odd
        ...     normal_version = ('''
        ...         def foo():
        ...             return 'bar'
        ...     ''')
        >>> assert normal_version != codeblock_version
        >>> print('Without codeblock')
        >>> print(normal_version)
        >>> print('With codeblock')
        >>> print(codeblock_version)
    """
    return textwrap.dedent(block_str).strip('\n')


class PythonPathContext(object):
    """
    Context for temporarilly adding a dir to the PYTHONPATH. Used in testing
    """
    def __init__(self, dpath):
        self.dpath = dpath

    def __enter__(self):
        sys.path.append(self.dpath)

    def __exit__(self, a, b, c):
        assert sys.path[-1] == self.dpath
        sys.path.pop()


class TempDir(object):
    """
    Context for creating and cleaning up temporary files. Used in testing.
    """
    def __init__(self):
        self.dpath = None

    def __enter__(self):
        import tempfile
        self.dpath = tempfile.mkdtemp()
        return self

    def __exit__(self, a, b, c):
        import shutil
        shutil.rmtree(self.dpath)


# def import_module_from_fpath(module_fpath):
#     """
#     imports module from a file path

#     Args:
#         module_fpath (str):

#     Returns:
#         module: module
#     """
#     from os.path import basename, splitext, isdir, join, exists, dirname, split
#     if isdir(module_fpath):
#         module_fpath = join(module_fpath, '__init__.py')
#     if not exists(module_fpath):
#         raise ImportError('module_fpath={!r} does not exist'.format(
#             module_fpath))
#     modname = splitext(basename(module_fpath))[0]
#     if modname == '__init__':
#         modname = split(dirname(module_fpath))[1]
#     if sys.version.startswith('2.7'):
#         import imp
#         module = imp.load_source(modname, module_fpath)
#     elif sys.version.startswith('3'):
#         import importlib.machinery
#         loader = importlib.machinery.SourceFileLoader(modname, module_fpath)
#         module = loader.load_module()
#         # module = loader.exec_module(modname)
#     else:
#         raise AssertionError('invalid python version={!r}'.format(
#             sys.version))
#     return module


def import_module_from_name(modname):
    r"""
    Args:
        modname (str):  module name

    Returns:
        module: module

    Example:
        >>> # test with modules that wont be imported in normal circumstances
        >>> # todo write a test where we gaurentee this
        >>> modname_list = [
        >>>     'test',
        >>>     'pickletools',
        >>>     'lib2to3.fixes.fix_apply',
        >>> ]
        >>> #assert not any(m in sys.modules for m in modname_list)
        >>> modules = [import_module_from_name(modname) for modname in modname_list]
        >>> assert [m.__name__ for m in modules] == modname_list
        >>> assert all(m in sys.modules for m in modname_list)
    """
    # The __import__ statment is weird
    if '.' in modname:
        fromlist = modname.split('.')[-1]
        fromlist_ = list(map(str, fromlist))  # needs to be ascii for python2.7
        module = __import__(modname, {}, {}, fromlist_, 0)
    else:
        module = __import__(modname, {}, {}, [], 0)
    return module

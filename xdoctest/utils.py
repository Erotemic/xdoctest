# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import re
import os
import sys
import six
import textwrap
from io import StringIO
from os.path import join, exists, normpath


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
        supress (bool): if True, stdout is not printed while captured
            (default = True)

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
    Highlights a block of text using ansi tags based on language syntax.

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

    Example:
        >>> with TempDir() as self:
        >>>     dpath = self.dpath
        >>>     assert exists(dpath)
        >>> assert not exists(dpath)

    Example:
        >>> self = TempDir()
        >>> dpath = self.ensure()
        >>> assert exists(dpath)
        >>> self.cleanup()
        >>> assert not exists(dpath)
    """
    def __init__(self):
        self.dpath = None

    def __del__(self):
        self.cleanup()

    def ensure(self):
        import tempfile
        if not self.dpath:
            self.dpath = tempfile.mkdtemp()
        return self.dpath

    def cleanup(self):
        import shutil
        if self.dpath:
            shutil.rmtree(self.dpath)
            self.dpath = None

    def __enter__(self):
        self.ensure()
        return self

    def __exit__(self, a, b, c):
        self.cleanup()


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


def import_module_from_path(modpath):
    """
    Args:
        modpath (str): path to the module

    References:
        https://stackoverflow.com/questions/67631/import-module-given-path

    Example:
        >>> from xdoctest import utils
        >>> modpath = utils.__file__
        >>> module = import_module_from_path(modpath)
        >>> assert module is utils
    """
    # the importlib version doesnt work in pytest
    import xdoctest.static_analysis as static
    dpath, rel_modpath = static.split_modpath(modpath)
    modname = static.modpath_to_modname(modpath)
    with PythonPathContext(dpath):
        module = import_module_from_name(modname)
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


def strip_ansi(text):
    r"""
    Removes all ansi directives from the string.

    References:
        http://stackoverflow.com/questions/14693701/remove-ansi
        https://stackoverflow.com/questions/13506033/filtering-out-ansi-escape-sequences

    Examples:
        >>> from xdoctest.utils import *
        >>> line = '\t\u001b[0;35mBlabla\u001b[0m     \u001b[0;36m172.18.0.2\u001b[0m'
        >>> escaped_line = strip_ansi(line)
        >>> assert escaped_line == '\tBlabla     172.18.0.2'
    """
    # ansi_escape1 = re.compile(r'\x1b[^m]*m')
    # text = ansi_escape1.sub('', text)
    # ansi_escape2 = re.compile(r'\x1b\[([0-9,A-Z]{1,2}(;[0-9]{1,2})?(;[0-9]{3})?)?[m|K]?')
    ansi_escape3 = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]', flags=re.IGNORECASE)
    text = ansi_escape3.sub('', text)
    return text


def ensuredir(dpath, mode=0o1777):
    r"""
    Ensures that directory will exist. creates new dir with sticky bits by
    default

    Args:
        dpath (str): dir to ensure. Can also be a tuple to send to join
        mode (int): octal mode of directory (default 0o1777)

    Returns:
        str: path - the ensured directory
    """
    if isinstance(dpath, (list, tuple)):  # nocover
        dpath = join(*dpath)
    if not exists(dpath):
        try:
            os.makedirs(normpath(dpath), mode=mode)
        except OSError:  # nocover
            raise
    return dpath


def color_text(text, color):
    r"""
    Colorizes text a single color using ansii tags.

    Args:
        text (str): text to colorize
        color (str): may be one of the following: yellow, blink, lightgray,
            underline, darkyellow, blue, darkblue, faint, fuchsia, black,
            white, red, brown, turquoise, bold, darkred, darkgreen, reset,
            standout, darkteal, darkgray, overline, purple, green, teal, fuscia

    Returns:
        str: text : colorized text.
            If pygments is not installed plain text is returned.

    Example:
        >>> text = 'raw text'
        >>> assert color_text(text, 'red') == '\x1b[31;01mraw text\x1b[39;49;00m'
        >>> assert color_text(text, None) == 'raw text'
    """
    if color is None:
        return text
    try:
        import pygments
        import pygments.console
        ansi_text = pygments.console.colorize(color, text)
        return ansi_text
    except ImportError:  # nocover
        import warnings
        warnings.warn('pygments is not installed')
        return text

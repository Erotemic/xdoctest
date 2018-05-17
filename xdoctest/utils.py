# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import warnings
import re
import os
import sys
import six
import textwrap
import io
import shutil
from os.path import join, exists, normpath


def ensure_unicode(text):
    """
    Casts bytes into utf8 (mostly for python2 compatibility)

    References:
        http://stackoverflow.com/questions/12561063/python-extract-data-from-file

    CommandLine:
        python -m xdoctest.utils ensure_unicode

    Example:
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


class TeeStringIO(io.StringIO):
    """ simple class to write to a stdout and a StringIO """
    def __init__(self, redirect=None):
        self.redirect = redirect
        super(TeeStringIO, self).__init__()

    def isatty(self):  # nocover
        """
        Returns true of the redirect is a terminal.

        Notes:
            Needed for IPython.embed to work properly when this class is used
            to override stdout / stderr.
        """
        return (self.redirect is not None and
                hasattr(self.redirect, 'isatty') and self.redirect.isatty())

    @property
    def encoding(self):
        if self.redirect is not None:
            return self.redirect.encoding
        else:
            return super(TeeStringIO, self).encoding

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
        >>> self = CaptureStdout(supress=True)
        >>> print('dont capture the table flip (╯°□°）╯︵ ┻━┻')
        >>> with self:
        ...     text = 'capture the heart ♥'
        ...     print(text)
        >>> print('dont capture look of disapproval ಠ_ಠ')
        >>> assert isinstance(self.text, six.text_type)
        >>> assert self.text == text + '\n', 'failed capture text'

    Example:
        >>> self = CaptureStdout(supress=False)
        >>> with self:
        ...     print('I am captured and printed in stdout')
        >>> assert self.text.strip() == 'I am captured and printed in stdout'

    Example:
        >>> self = CaptureStdout(supress=True, enabled=False)
        >>> with self:
        ...     print('dont capture')
        >>> assert self.text is None
    """
    def __init__(self, supress=True, enabled=True):
        self.enabled = enabled
        self.supress = supress
        self.orig_stdout = sys.stdout
        if supress:
            redirect = None
        else:
            redirect = self.orig_stdout
        self.cap_stdout = TeeStringIO(redirect)
        self.text = None

        self._pos = 0  # keep track of how much has been logged
        self.parts = []
        self.started = False

    def log_part(self):
        """ Log what has been captured so far """
        self.cap_stdout.seek(self._pos)
        text = self.cap_stdout.read()
        self._pos = self.cap_stdout.tell()
        self.parts.append(text)
        self.text = text

    def start(self):
        if self.enabled:
            self.text = ''
            self.started = True
            sys.stdout = self.cap_stdout

    def stop(self):
        if self.enabled:
            self.started = False
            sys.stdout = self.orig_stdout

    def __enter__(self):
        self.start()
        return self

    def __del__(self):
        if self.started:
            self.stop()
        if self.cap_stdout is not None:
            self.close()

    def close(self):
        self.cap_stdout.close()
        self.cap_stdout = None

    def __exit__(self, type_, value, trace):
        if self.enabled:
            try:
                self.log_part()
            except Exception:  # nocover
                raise
            finally:
                self.stop()
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
        python -m xdoctest.utils ensure_unicode

    Example:
        >>> text = 'Lorem ipsum\ndolor sit amet'
        >>> prefix = '    '
        >>> result = indent(text, prefix)
        >>> assert all(t.startswith(prefix) for t in result.split('\n'))
    """
    return prefix + text.replace('\n', '\n' + prefix)


def highlight_code(text, lexer_name='python', **kwargs):
    """
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
    """
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
        if len(sys.path) <= self.index or sys.path[self.index] != self.dpath:
            raise AssertionError(
                'sys.path significantly changed while in PythonPathContext')
        sys.path.pop(self.index)


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
    def __init__(self, persist=False):
        self.dpath = None
        self.persist = persist

    def __del__(self):
        self.cleanup()

    def ensure(self):
        import tempfile
        if not self.dpath:
            self.dpath = tempfile.mkdtemp()
        return self.dpath

    def cleanup(self):
        if not self.persist:
            if self.dpath:
                shutil.rmtree(self.dpath)
                self.dpath = None

    def __enter__(self):
        self.ensure()
        return self

    def __exit__(self, type_, value, trace):
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
        try:
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
    """
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

        if sys.platform.startswith('win32'):  # nocover
            # Hack on win32 to support colored output
            import colorama
            colorama.init()

        ansi_text = pygments.console.colorize(color, text)
        return ansi_text
    except ImportError:  # nocover
        warnings.warn('pygments is not installed')
        return text


class NiceRepr(object):
    """
    Defines `__str__` and `__repr__` in terms of `__nice__` function
    Classes that inherit `NiceRepr` must define `__nice__`

    Example:
        >>> class Foo(NiceRepr):
        ...    pass
        >>> class Bar(NiceRepr):
        ...    def __nice__(self):
        ...        return 'info'
        >>> foo = Foo()
        >>> bar = Bar()
        >>> assert str(bar) == '<Bar(info)>'
        >>> assert repr(bar).startswith('<Bar(info) at ')
        >>> assert 'object at' in str(foo)
        >>> assert 'object at' in repr(foo)
    """
    def __repr__(self):
        try:
            classname = self.__class__.__name__
            devnice = self.__nice__()
            return '<%s(%s) at %s>' % (classname, devnice, hex(id(self)))
        except AttributeError:
            if hasattr(self, '__nice__'):
                raise
            # warnings.warn('Define the __nice__ method for %r' %
            #               (self.__class__,), category=RuntimeWarning)
            return object.__repr__(self)
            #return super(NiceRepr, self).__repr__()

    def __str__(self):
        try:
            classname = self.__class__.__name__
            devnice = self.__nice__()
            return '<%s(%s)>' % (classname, devnice)
        except AttributeError:
            if hasattr(self, '__nice__'):
                raise
            # warnings.warn('Define the __nice__ method for %r' %
            #               (self.__class__,), category=RuntimeWarning)
            return object.__str__(self)
            #return super(NiceRepr, self).__str__()


class TempDoctest(object):
    """
    Creates a temporary file containing a doctest for testing
    """

    def __init__(self, modname, docstr):
        self.modname = modname
        self.docstr = docstr
        self.temp = TempDir()
        self.dpath = self.temp.ensure()
        self.modpath = join(self.dpath, self.modname + '.py')
        with open(self.modpath, 'w') as file:
            file.write("'''\n%s'''" % self.docstr)

if __name__ == '__main__':
    """
    CommandLine:
        python -m xdoctest.utils all
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

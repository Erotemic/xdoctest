# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import six
import codecs
from six.moves import cStringIO as StringIO


class TeeStringIO(StringIO):
    """ simple class to write to a stdout and a StringIO """
    def __init__(self, redirect=None):
        self.redirect = redirect
        super(TeeStringIO, self).__init__()

    def write(self, msg):
        if self.redirect is not None:
            self.redirect.write(msg)
        super(TeeStringIO, self).write(msg)

    def flush(self, msg):
        if self.redirect is not None:
            self.redirect.flush(msg)
        super(TeeStringIO, self).flush(msg)


class CaptureStdout(object):
    r"""
    Context manager that captures stdout and stores it in an internal stream

    Args:
        enabled (bool): (default = True)

    Example:
        >>> from doctest2.utils import *
        >>> self = CaptureStdout(enabled=True)
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
        if six.PY2:
            # http://stackoverflow.com/questions/1817695/stringio-accept-utf8
            codecinfo = codecs.lookup('utf8')
            self.cap_stdout = codecs.StreamReaderWriter(
                self.cap_stdout, codecinfo.streamreader,
                codecinfo.streamwriter)
        self.text = None

    def __enter__(self):
        sys.stdout = self.cap_stdout
        return self

    def __exit__(self, type_, value, trace):
        try:
            self.cap_stdout.seek(0)
            self.text = self.cap_stdout.read()
            if six.PY2:
                self.text = self.text.decode('utf8')
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

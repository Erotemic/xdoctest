# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import six
import codecs
from six.moves import cStringIO


class CaptureStdout(object):
    r"""
    Context manager that captures stdout and stores it in an internal stream

    Args:
        enabled (bool): (default = True)

    Example:
        >>> self = CaptureStdout(enabled=True)
        >>> print('dont capture the table flip (╯°□°）╯︵ ┻━┻')
        >>> with self:
        ...     print('capture the heart ♥')
        >>> print('dont capture look of disapproval ಠ_ಠ')
        >>> assert isinstance(self.text, six.text_type)
        >>> assert self.text == 'capture the heart ♥\n', 'failed capture text'
    """
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.orig_stdout = sys.stdout
        self.cap_stdout = cStringIO()
        if six.PY2:
            # http://stackoverflow.com/questions/1817695/stringio-accept-utf8
            codecinfo = codecs.lookup('utf8')
            self.cap_stdout = codecs.StreamReaderWriter(
                self.cap_stdout, codecinfo.streamreader,
                codecinfo.streamwriter)
        self.text = None

    def __enter__(self):
        if self.enabled:
            sys.stdout = self.cap_stdout
        return self

    def __exit__(self, type_, value, trace):
        if self.enabled:
            try:
                self.cap_stdout.seek(0)
                self.text = self.cap_stdout.read()
                if six.PY2:
                    self.text = self.text.decode('utf8')
            except Exception:  # nocover
                pass
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

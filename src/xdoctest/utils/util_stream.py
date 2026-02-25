"""
Functions for capturing and redirecting IO streams.

The :class:`CaptureStdout` captures all text sent to stdout and optionally
prevents it from actually reaching stdout.

The :class:`TeeStringIO` does the same thing but for arbitrary streams. It is
how the former is implemented.

"""

from __future__ import annotations

import sys
import io
import typing


class TeeStringIO(io.StringIO):
    """
    An IO object that writes to itself and another IO stream.

    Attributes:
        redirect (io.IOBase): The other stream to write to.

    Example:
        >>> redirect = io.StringIO()
        >>> self = TeeStringIO(redirect)
    """

    def __init__(self, redirect: io.IOBase | None = None) -> None:
        self.redirect: io.IOBase | None = redirect
        super(TeeStringIO, self).__init__()

        # Logic taken from prompt_toolkit/output/vt100.py version 3.0.5 in
        # flush I don't have a full understanding of what the buffer
        # attribute is supposed to be capturing here, but this seems to
        # allow us to embed in IPython while still capturing and Teeing
        # stdout
        if hasattr(redirect, 'buffer'):
            object.__setattr__(
                self, 'buffer', typing.cast(typing.Any, redirect).buffer
            )
        else:
            object.__setattr__(
                self, 'buffer', typing.cast(typing.Any, redirect)
            )

    def isatty(self) -> bool:  # nocover
        """
        Returns true of the redirect is a terminal.

        Note:
            Needed for IPython.embed to work properly when this class is used
            to override stdout / stderr.
        """
        return (
            self.redirect is not None
            and hasattr(self.redirect, 'isatty')
            and self.redirect.isatty()
        )

    def fileno(self) -> int:
        """
        Returns underlying file descriptor of the redirected IOBase object
        if one exists.
        """
        if self.redirect is not None:
            return self.redirect.fileno()
        else:
            return super(TeeStringIO, self).fileno()

    @property
    def encoding(self):
        """
        Gets the encoding of the `redirect` IO object

        Example:
            >>> redirect = io.StringIO()
            >>> assert TeeStringIO(redirect).encoding is None
            >>> assert TeeStringIO(None).encoding is None
            >>> assert TeeStringIO(sys.stdout).encoding is sys.stdout.encoding
            >>> redirect = io.TextIOWrapper(io.StringIO())
            >>> assert TeeStringIO(redirect).encoding is redirect.encoding
        """
        if self.redirect is not None:
            return self.redirect.encoding
        else:
            return super(TeeStringIO, self).encoding

    def write(self, msg: str) -> int:
        """
        Write to this and the redirected stream
        """
        if self.redirect is not None:
            self.redirect.write(msg)
        return super(TeeStringIO, self).write(msg)

    def flush(self):  # nocover
        """
        Flush to this and the redirected stream
        """
        if self.redirect is not None:
            self.redirect.flush()
        return super(TeeStringIO, self).flush()


class CaptureStream:
    """
    Generic class for capturing streaming output from stdout or stderr
    """


class CaptureStdout(CaptureStream):
    r"""
    Context manager that captures stdout and stores it in an internal stream

    Args:
        suppress (bool, default=True):
            if True, stdout is not printed while captured
        enabled (bool, default=True):
            does nothing if this is False

    Example:
        >>> self = CaptureStdout(suppress=True)
        >>> print('dont capture the table flip (╯°□°）╯︵ ┻━┻')
        >>> with self:
        ...     text = 'capture the heart ♥'
        ...     print(text)
        >>> print('dont capture look of disapproval ಠ_ಠ')
        >>> assert isinstance(self.text, str)
        >>> assert self.text == text + '\n', 'failed capture text'

    Example:
        >>> self = CaptureStdout(suppress=False)
        >>> with self:
        ...     print('I am captured and printed in stdout')
        >>> assert self.text.strip() == 'I am captured and printed in stdout'

    Example:
        >>> self = CaptureStdout(suppress=True, enabled=False)
        >>> with self:
        ...     print('dont capture')
        >>> assert self.text is None
    """

    def __init__(
        self, suppress: bool = True, enabled: bool = True, **kwargs: object
    ) -> None:
        _misspelled_varname = 'supress'
        if _misspelled_varname in kwargs:  # nocover
            from xdoctest.utils import util_deprecation

            util_deprecation.schedule_deprecation(
                modname='xdoctest',
                name='supress',
                type='Argument of CaptureStdout',
                migration='Use suppress instead',
                deprecate='1.0.0',
                error='1.1.0',
                remove='1.2.0',
            )
            suppress = bool(kwargs.pop(_misspelled_varname))
            if len(kwargs) > 0:
                raise ValueError('unexpected args: {}'.format(kwargs))
        self.enabled = enabled
        self.suppress = suppress
        self.orig_stdout = sys.stdout
        if suppress:
            redirect = None
        else:
            redirect = self.orig_stdout
        self.cap_stdout: TeeStringIO | None = TeeStringIO(
            typing.cast(io.IOBase | None, redirect)
        )
        self.text: str | None = None

        self._pos = 0  # keep track of how much has been logged
        self.parts: list[str] = []
        self.started = False

    def log_part(self) -> None:
        """Log what has been captured so far"""
        assert self.cap_stdout is not None
        self.cap_stdout.seek(self._pos)
        text = self.cap_stdout.read()
        self._pos = self.cap_stdout.tell()
        self.parts.append(text)
        self.text = text

    def start(self) -> None:
        if self.enabled:
            assert self.cap_stdout is not None
            self.text = ''
            self.started = True
            sys.stdout = self.cap_stdout

    def stop(self) -> None:
        """
        Example:
            >>> CaptureStdout(enabled=False).stop()
            >>> CaptureStdout(enabled=True).stop()
        """
        if self.enabled:
            self.started = False
            sys.stdout = self.orig_stdout

    def __enter__(self) -> CaptureStdout:
        self.start()
        return self

    def __del__(self) -> None:  # nocover
        if self.started:
            self.stop()
        if self.cap_stdout is not None:
            self.close()

    def close(self) -> None:
        if self.cap_stdout is not None:
            self.cap_stdout.close()
            self.cap_stdout = None

    def __exit__(self, type_: object, value: object, trace: object) -> None:
        if self.enabled:
            try:
                self.log_part()
            except Exception:  # nocover
                raise
            finally:
                self.stop()
        if trace is not None:
            return None  # return a falsey value on error

"""
Utilities related to filesystem paths
"""
import os
from os.path import exists
from os.path import join
from os.path import normpath
import shutil


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
        import sys
        if not self.dpath:
            dpath = tempfile.mkdtemp()
            if sys.platform.startswith('win32'):
                # Force a long path
                # References:
                # https://stackoverflow.com/questions/11420689/how-to-get-long-file-system-path-from-python-on-windows
                from ctypes import create_unicode_buffer, windll
                BUFFER_SIZE = 500
                buffer = create_unicode_buffer(BUFFER_SIZE)
                get_long_path_name = windll.kernel32.GetLongPathNameW
                get_long_path_name(dpath, buffer, BUFFER_SIZE)
                dpath = buffer.value
            self.dpath = dpath
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

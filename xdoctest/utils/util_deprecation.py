"""
Utilities for helping robustly deprecate features.
"""
import warnings


DEP_SCHEDULE_1 = dict(deprecate='0.9.6', remove='1.0.0')


def paragraph(text):
    r"""
    Wraps multi-line strings and restructures the text to remove all newlines,
    heading, trailing, and double spaces.

    Useful for writing log messages

    Args:
        text (str): typically a multiline string

    Returns:
        str: the reduced text block

    Example:
        >>> import ubelt as ub
        >>> text = (
        >>>     '''
        >>>     Lorem ipsum dolor sit amet, consectetur adipiscing
        >>>     elit, sed do eiusmod tempor incididunt ut labore et
        >>>     dolore magna aliqua.
        >>>     ''')
        >>> out = ub.paragraph(text)
        >>> assert chr(10) in text
        >>> assert chr(10) not in out
        >>> print('text = {!r}'.format(text))
        >>> print('out = {!r}'.format(out))
    """
    import re
    out = re.sub(r'\s\s*', ' ', text).strip()
    return out


def schedule_deprecation3(modname, migration='', name='?', type='?', deprecate=None, error=None, remove=None):  # nocover
    """
    Deprecation machinery to help provide users with a smoother transition.
    """
    import sys
    from distutils.version import LooseVersion
    module = sys.modules[modname]
    current = LooseVersion(module.__version__)
    deprecate = None if deprecate is None else LooseVersion(deprecate)
    remove = None if remove is None else LooseVersion(remove)
    error = None if error is None else LooseVersion(error)
    if deprecate is None or current >= deprecate:
        if migration is None:
            migration = ''
        msg = paragraph(
            '''
            The "{name}" {type} was deprecated in {deprecate}, will cause
            an error in {error} and will be removed in {remove}. The current
            version is {current}. {migration}
            ''').format(**locals()).strip()
        if remove is not None and current >= remove:
            raise AssertionError('forgot to remove a deprecated function')
        if error is not None and current >= error:
            raise DeprecationWarning(msg)
        else:
            warnings.warn(msg, DeprecationWarning)

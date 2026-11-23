"""
Utilities for helping robustly deprecate features.
"""

from __future__ import annotations


def schedule_deprecation(
    modname: str,
    name: str = '?',
    type: str = '?',
    migration: str = '',
    deprecate: str | None = None,
    error: str | None = None,
    remove: str | None = None,
) -> None:
    """
    Deprecation machinery to help provide users with a smoother transition.

    This function provides a concise way to mark a feature as deprecated by
    providing a description of the deprecated feature, documentation on how to
    migrate away from the deprecated feature, and the versions that the feature
    is scheduled for deprecation and eventual removal. Based on the version of
    the library and the specified schedule this function will either do
    nothing, emit a warning, or raise an error with helpful messages for both
    users and developers.

    Args:
        modname (str):
            The name of the underlying module associated with the feature to be
            deprecated. The module must already be imported and have a passable
            ``__version__`` attribute.

        name (str):
            The name of the feature to deprecate. This is usually a function or
            argument name.

        type (str):
            A description of what the feature is. This is not a formal type,
            but rather a prose description: e.g. "argument to my_func".

        migration (str):
            A description that lets users know what they should do instead of
            using the deprecated feature.

        deprecate (str | None):
            The version when the feature is officially deprecated and this
            function should start to emit a deprecation warning.

        error (str | None):
            The version when the feature is officially no longer supported, and
            will start to raise a RuntimeError.

        remove (str | None):
            The version when the feature is completely removed. An
            AssertionError will be raised if this function is still present
            reminding the developer to remove the feature (or extend the remove
            version).

    Note:
        The :class:`DeprecationWarning` is not visible by default.
        https://docs.python.org/3/library/warnings.html

    Example:
        >>> import sys
        >>> import types
        >>> import pytest
        >>> dummy_module = sys.modules['dummy_module'] = types.ModuleType('dummy_module')
        >>> # When less than the deprecated version this does nothing
        >>> dummy_module.__version__ = '1.0.0'
        >>> schedule_deprecation(
        ...     'dummy_module', 'myfunc', 'function', 'do something else',
        ...     deprecate='1.1.0', error='1.2.0', remove='1.3.0')
        >>> # Now this raises warning
        >>> with pytest.warns(DeprecationWarning):
        ...     dummy_module.__version__ = '1.1.0'
        ...     schedule_deprecation(
        ...         'dummy_module', 'myfunc', 'function', 'do something else',
        ...         deprecate='1.1.0', error='1.2.0', remove='1.3.0')
        >>> # Now this raises an error for the user
        >>> with pytest.raises(RuntimeError):
        ...     dummy_module.__version__ = '1.2.0'
        ...     schedule_deprecation(
        ...         'dummy_module', 'myfunc', 'function', 'do something else',
        ...         deprecate='1.1.0', error='1.2.0', remove='1.3.0')
        >>> # Now this raises an error for the developer
        >>> with pytest.raises(AssertionError):
        ...     dummy_module.__version__ = '1.3.0'
        ...     schedule_deprecation(
        ...         'dummy_module', 'myfunc', 'function', 'do something else',
        ...         deprecate='1.1.0', error='1.2.0', remove='1.3.0')
        >>> # When no versions are specified, it simply emits the warning
        >>> with pytest.warns(DeprecationWarning):
        ...     dummy_module.__version__ = '1.1.0'
        ...     schedule_deprecation(
        ...         'dummy_module', 'myfunc', 'function', 'do something else')
    """
    import sys
    import warnings
    from collections.abc import Callable
    from typing import Any

    # Both branches parse all versions with the same implementation. Their
    # concrete return types differ, so use a common callable annotation rather
    # than an invalid Version | LooseVersion comparison.
    _parse_version: Callable[[str], Any]
    try:
        import packaging.version as _pkg_version

        _parse_version = _pkg_version.parse
    except ImportError:
        import distutils.version as _dist_version  # type: ignore[unresolved-import]

        _parse_version = _dist_version.LooseVersion

    # Keep the comparison within a single version backend. Each constructor
    # has its own ordering protocol, so comparing a union of their return
    # types is not valid to a static checker (or across backends at runtime).
    def _at_least(actual: str, threshold: str) -> bool:
        try:
            import packaging.version as pkg_version
        except ImportError:
            import distutils.version as dist_version  # type: ignore[unresolved-import]

            return dist_version.LooseVersion(actual) >= dist_version.LooseVersion(
                threshold
            )
        return pkg_version.parse(actual) >= pkg_version.parse(threshold)

    module = sys.modules[modname]
    current_text = module.__version__
    current = _parse_version(current_text)
    deprecate_v = _parse_version(deprecate) if deprecate is not None else None
    remove_v = _parse_version(remove) if remove is not None else None
    error_v = _parse_version(error) if error is not None else None
    deprecate_str = '' if deprecate_v is None else f' in {deprecate_v}'
    remove_str = '' if remove_v is None else f' in {remove_v}'
    error_str = '' if error_v is None else f' in {error_v}'
    if deprecate is None or _at_least(current_text, deprecate):
        msg = (
            (
                'The "{name}" {type} was deprecated{deprecate_str}, will cause '
                'an error{error_str} and will be removed{remove_str}. The current '
                'version is {current}. {migration}'
            )
            .format(**locals())
            .strip()
        )
        if remove is not None and _at_least(current_text, remove):
            raise AssertionError(
                'Forgot to remove deprecated: '
                + msg
                + ' '
                + 'Remove the function, or extend the scheduled remove version.'
            )
        if error is not None and _at_least(current_text, error):
            raise RuntimeError(msg)
        else:
            warnings.warn(msg, DeprecationWarning)

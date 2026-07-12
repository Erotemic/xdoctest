"""
Small context managers for controlling warning behavior.
"""

from __future__ import annotations

import warnings
from types import TracebackType


class IgnoreWarnings:
    """
    Temporarily silence warnings without changing the surrounding filter state.

    Example:
        >>> import warnings
        >>> with warnings.catch_warnings():
        >>>     warnings.simplefilter('error')
        >>>     with IgnoreWarnings():
        >>>         warnings.warn('hidden')
    """

    def __init__(self) -> None:
        self._catcher: warnings.catch_warnings | None = None

    def __enter__(self) -> IgnoreWarnings:
        if self._catcher is not None:
            raise RuntimeError('warning context cannot be re-entered while active')
        catcher = warnings.catch_warnings()
        catcher.__enter__()
        self._catcher = catcher
        warnings.simplefilter('ignore')
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        catcher = self._catcher
        if catcher is None:
            raise RuntimeError('warning context is not active')
        self._catcher = None
        catcher.__exit__(exc_type, exc_value, traceback)


class ShowWarnings:
    """
    Capture warnings and print them as ``Category: message`` lines on exit.

    Example:
        >>> import warnings
        >>> with ShowWarnings():
        >>>     warnings.warn('visible')
        UserWarning: visible
    """

    def __init__(self) -> None:
        self._catcher: warnings.catch_warnings | None = None
        self.captured: list[warnings.WarningMessage] = []

    def __enter__(self) -> ShowWarnings:
        if self._catcher is not None:
            raise RuntimeError('warning context cannot be re-entered while active')
        catcher = warnings.catch_warnings(record=True)
        captured = catcher.__enter__()
        assert captured is not None
        self._catcher = catcher
        self.captured = captured
        warnings.simplefilter('always')
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        catcher = self._catcher
        if catcher is None:
            raise RuntimeError('warning context is not active')
        self._catcher = None
        catcher.__exit__(exc_type, exc_value, traceback)
        if exc_type is None:
            for warn in self.captured:
                category_name = getattr(
                    warn, '_category_name', warn.category.__name__
                )
                print(f'{category_name}: {warn.message}')


__all__ = ['IgnoreWarnings', 'ShowWarnings']

from __future__ import annotations

import doctest
from typing import Dict, cast

from xdoctest import directive

BLANKLINE_MARKER = doctest.BLANKLINE_MARKER
ELLIPSIS_MARKER = doctest.ELLIPSIS_MARKER

DONT_ACCEPT_BLANKLINE = doctest.DONT_ACCEPT_BLANKLINE
NORMALIZE_WHITESPACE = doctest.NORMALIZE_WHITESPACE
ELLIPSIS = doctest.ELLIPSIS
IGNORE_EXCEPTION_DETAIL = doctest.IGNORE_EXCEPTION_DETAIL
REPORT_UDIFF = doctest.REPORT_UDIFF
REPORT_CDIFF = doctest.REPORT_CDIFF
REPORT_NDIFF = doctest.REPORT_NDIFF


class RuntimeFlagFacade:
    def __init__(self) -> None:
        self._optionflags_by_name: Dict[str, int] = {}
        self._optionflag_names_by_value: Dict[int, str] = {}
        self._runtime_key_to_optionflag: Dict[str, int] = {}
        self._optionflag_to_runtime_key: Dict[int, str] = {}

    def register_builtin_optionflag(
        self,
        name: str,
        flag: int,
        runtime_state_key: str | None = None,
    ) -> int:
        self._optionflags_by_name[name] = flag
        self._optionflag_names_by_value[flag] = name
        if runtime_state_key is not None:
            self._runtime_key_to_optionflag[runtime_state_key] = flag
            self._optionflag_to_runtime_key[flag] = runtime_state_key
        return flag

    def register_optionflag(
        self,
        name: str,
        runtime_state_key: str | None = None,
    ) -> int:
        if name in self._optionflags_by_name:
            flag = self._optionflags_by_name[name]
            if runtime_state_key is not None:
                self._runtime_key_to_optionflag[runtime_state_key] = flag
                self._optionflag_to_runtime_key[flag] = runtime_state_key
            return flag
        flag = doctest.register_optionflag(name)
        return self.register_builtin_optionflag(name, flag, runtime_state_key)

    def is_registered_optionflag(self, name: str) -> bool:
        return name in self._optionflags_by_name

    def get_optionflag(self, name: str) -> int:
        return self._optionflags_by_name[name]

    def get_registered_optionflags(self) -> Dict[str, int]:
        return dict(self._optionflags_by_name)

    def _runtime_bound_optionflag_mask(self) -> int:
        """Return the mask represented by structured runtime-state keys."""
        mask = 0
        for flag in self._optionflag_to_runtime_key:
            mask |= flag
        return mask

    def runtime_state_to_optionflags(
        self,
        runstate: directive.RuntimeState | dict | None,
    ) -> int:
        runtime_bound_mask = self._runtime_bound_optionflag_mask()
        flags = 0
        if isinstance(runstate, directive.RuntimeState):
            flags |= runstate.get_output_checker_flags() & ~runtime_bound_mask
            lookup = runstate.__getitem__
        elif runstate is None:
            runstate = directive.RuntimeState()
            flags |= runstate.get_output_checker_flags() & ~runtime_bound_mask
            lookup = runstate.__getitem__
        else:
            lookup = runstate.__getitem__
            if isinstance(runstate, dict):
                flags |= int(runstate.get('_optionflags', 0)) & ~runtime_bound_mask

        for runtime_key, flag in self._runtime_key_to_optionflag.items():
            try:
                value = lookup(runtime_key)
            except KeyError:
                continue
            if isinstance(value, bool) and value:
                flags |= flag
        return flags

    def optionflags_to_runtime_state(
        self,
        optionflags: int,
        default_state: directive.RuntimeStateDict | None = None,
    ) -> directive.RuntimeState:
        base_state = {} if default_state is None else dict(default_state)
        for runtime_key in self._runtime_key_to_optionflag:
            if runtime_key == 'REQUIRES':
                continue
            base_state.setdefault(runtime_key, False)
        runstate = directive.RuntimeState(
            cast(directive.RuntimeStateDict, base_state)
        )
        runtime_bound_mask = self._runtime_bound_optionflag_mask()
        checker_only_flags = optionflags & ~runtime_bound_mask
        runstate.set_output_checker_flags(checker_only_flags)
        for flag, runtime_key in self._optionflag_to_runtime_key.items():
            value = runstate[runtime_key]
            if isinstance(value, bool) and (optionflags & flag):
                runstate[runtime_key] = True
        return runstate


_RUNTIME_FLAGS = RuntimeFlagFacade()


def register_optionflag(name: str, runtime_state_key: str | None = None) -> int:
    return _RUNTIME_FLAGS.register_optionflag(name, runtime_state_key)


def runtime_state_to_optionflags(
    runstate: directive.RuntimeState | dict | None,
) -> int:
    return _RUNTIME_FLAGS.runtime_state_to_optionflags(runstate)


def optionflags_to_runtime_state(
    optionflags: int,
    default_state: directive.RuntimeStateDict | None = None,
) -> directive.RuntimeState:
    return _RUNTIME_FLAGS.optionflags_to_runtime_state(optionflags, default_state)


def is_registered_optionflag(name: str) -> bool:
    return _RUNTIME_FLAGS.is_registered_optionflag(name)


def get_optionflag(name: str) -> int:
    return _RUNTIME_FLAGS.get_optionflag(name)


def get_registered_optionflags() -> Dict[str, int]:
    return _RUNTIME_FLAGS.get_registered_optionflags()


_RUNTIME_FLAGS.register_builtin_optionflag(
    'DONT_ACCEPT_BLANKLINE', DONT_ACCEPT_BLANKLINE, 'DONT_ACCEPT_BLANKLINE'
)
_RUNTIME_FLAGS.register_builtin_optionflag(
    'NORMALIZE_WHITESPACE', NORMALIZE_WHITESPACE, 'NORMALIZE_WHITESPACE'
)
_RUNTIME_FLAGS.register_builtin_optionflag('ELLIPSIS', ELLIPSIS, 'ELLIPSIS')
_RUNTIME_FLAGS.register_builtin_optionflag(
    'IGNORE_EXCEPTION_DETAIL',
    IGNORE_EXCEPTION_DETAIL,
    'IGNORE_EXCEPTION_DETAIL',
)
_RUNTIME_FLAGS.register_builtin_optionflag('REPORT_UDIFF', REPORT_UDIFF, 'REPORT_UDIFF')
_RUNTIME_FLAGS.register_builtin_optionflag('REPORT_CDIFF', REPORT_CDIFF, 'REPORT_CDIFF')
_RUNTIME_FLAGS.register_builtin_optionflag('REPORT_NDIFF', REPORT_NDIFF, 'REPORT_NDIFF')
IGNORE_WANT = register_optionflag('IGNORE_WANT', 'IGNORE_WANT')
IGNORE_OUTPUT = register_optionflag('IGNORE_OUTPUT', 'IGNORE_OUTPUT')
IGNORE_WHITESPACE = register_optionflag('IGNORE_WHITESPACE', 'IGNORE_WHITESPACE')
FLOAT_CMP = register_optionflag('FLOAT_CMP', 'FLOAT_CMP')
NORMALIZE_REPR = register_optionflag('NORMALIZE_REPR', 'NORMALIZE_REPR')


__all__ = [
    'BLANKLINE_MARKER',
    'ELLIPSIS_MARKER',
    'DONT_ACCEPT_BLANKLINE',
    'NORMALIZE_WHITESPACE',
    'ELLIPSIS',
    'IGNORE_EXCEPTION_DETAIL',
    'REPORT_UDIFF',
    'REPORT_CDIFF',
    'REPORT_NDIFF',
    'IGNORE_WANT',
    'IGNORE_OUTPUT',
    'IGNORE_WHITESPACE',
    'FLOAT_CMP',
    'NORMALIZE_REPR',
    'register_optionflag',
    'runtime_state_to_optionflags',
    'optionflags_to_runtime_state',
    'is_registered_optionflag',
    'get_optionflag',
    'get_registered_optionflags',
]

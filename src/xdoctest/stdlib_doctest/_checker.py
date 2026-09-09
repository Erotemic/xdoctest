"""
Stdlib-doctest-shaped checker adapter for xdoctest.

This module exposes a small public surface that lets tooling built around the
stdlib :mod:`doctest` module (most notably :mod:`pytest_doctestplus`) plug
into xdoctest's runner without having to know about xdoctest's internal
:class:`~xdoctest.directive.RuntimeState`.

Adopters typically:

1. Register their optionflags through :func:`xdoctest.stdlib_doctest.register_optionflag`.
2. Define an :class:`OutputChecker` subclass with the standard
   ``check_output(want, got, optionflags)`` and (optionally)
   ``output_difference(example, got, optionflags)`` signatures.
3. Register the checker by name with :func:`register_checker`.
4. Select the checker for a given doctest by setting
   ``DoctestConfig['output_checker']`` to that name.

The name ``'xdoctest'`` is reserved for the native checker. Foreign checker
registrations use every other name.
"""

from __future__ import annotations

import doctest
from collections.abc import Mapping
from dataclasses import dataclass

from xdoctest import checker, directive
from ._optionflags import (
    optionflags_to_runtime_state,
    register_optionflag,
    runtime_state_to_optionflags,
)

_NATIVE_CHECKER_NAME = 'xdoctest'


@dataclass(frozen=True)
class _CheckerRegistration:
    """One immutable registry generation for a foreign checker name."""

    checker: doctest.OutputChecker | type[doctest.OutputChecker]


# Keep this union inside postponed annotations. A module-level assignment such
# as ``CheckerLike = OutputChecker | type[OutputChecker]`` would evaluate the
# PEP 604 expression during import and break supported Python 3.8 / 3.9.
_REGISTERED_CHECKERS: dict[str, _CheckerRegistration] = {}


def register_checker(
    name: str,
    checker_: doctest.OutputChecker | type[doctest.OutputChecker],
) -> None:
    """
    Register a foreign output checker under a configuration name.

    Args:
        name: selection key used in configs and runtime state. ``'xdoctest'``
            is reserved for the native checker and cannot be replaced.
        checker_: either an :class:`doctest.OutputChecker` instance or a class
            with a no-argument constructor that returns one. Instances are
            explicitly process-shared. Classes retain factory semantics and
            are materialized at most once for each :class:`RuntimeState` run.

    Example:
        >>> import doctest
        >>> name = '_xdoctest_example_checker'
        >>> instance = doctest.OutputChecker()
        >>> register_checker(name, instance)
        >>> resolve_checker(name) is instance
        True
        >>> del _REGISTERED_CHECKERS[name]
    """
    if name == _NATIVE_CHECKER_NAME:
        raise ValueError(
            "'xdoctest' is reserved for the native output checker"
        )
    _REGISTERED_CHECKERS[name] = _CheckerRegistration(checker_)


def resolve_checker(
    name: str,
    runstate: directive.RuntimeState | None = None,
) -> doctest.OutputChecker:
    """
    Resolve an output checker using the documented registration lifecycle.

    The reserved native checker is constructed directly and is never stored in
    the mutable foreign registry. Registered instances are returned as-is.
    Registered classes are factories when no runtime state is supplied. With a
    runtime state, one instance is cached for that run and reused by matching
    and failure rendering. A fresh registration record invalidates an existing
    per-run cache even when the same class is registered again.

    Raises:
        KeyError: if a foreign name has not been registered.

    Example:
        >>> isinstance(resolve_checker('xdoctest'), OutputChecker)
        True

    Example:
        >>> class ExampleChecker(doctest.OutputChecker):
        >>>     pass
        >>> name = '_xdoctest_per_run_checker_example'
        >>> register_checker(name, ExampleChecker)
        >>> resolve_checker(name) is resolve_checker(name)
        False
        >>> state = directive.RuntimeState()
        >>> state.set_output_checker(name)
        >>> resolve_checker(name, state) is resolve_checker(name, state)
        True
        >>> del _REGISTERED_CHECKERS[name]
    """
    if name == _NATIVE_CHECKER_NAME:
        return OutputChecker()
    if name not in _REGISTERED_CHECKERS:
        known = sorted([_NATIVE_CHECKER_NAME, *_REGISTERED_CHECKERS])
        raise KeyError(
            'Unknown output checker {!r}. Known checkers are {}'.format(
                name, known
            )
        )
    registration = _REGISTERED_CHECKERS[name]
    checker_ = registration.checker
    if isinstance(checker_, doctest.OutputChecker):
        return checker_
    if runstate is None:
        return checker_()
    instance = runstate.get_cached_output_checker(registration)
    if instance is None:
        instance = checker_()
        runstate.cache_output_checker(registration, instance)
    return instance


def resolve_current_checker(
    runstate: directive.RuntimeState | Mapping[str, object] | None,
) -> doctest.OutputChecker:
    """
    Return the checker selected by the given runtime state.

    A real :class:`RuntimeState` supplies the bounded execution lifetime used
    for class registrations. Plain mappings have no run lifetime, so class
    registrations retain direct factory semantics for those calls.

    Example:
        >>> checker = resolve_current_checker({'_output_checker': 'xdoctest'})
        >>> isinstance(checker, OutputChecker)
        True
    """
    if isinstance(runstate, directive.RuntimeState):
        checker_name = runstate.get_output_checker()
        return resolve_checker(checker_name, runstate)
    if isinstance(runstate, Mapping):
        checker_name = str(runstate.get('_output_checker', _NATIVE_CHECKER_NAME))
    else:
        checker_name = _NATIVE_CHECKER_NAME
    return resolve_checker(checker_name)


class OutputChecker(doctest.OutputChecker):
    r"""
    Default xdoctest checker exposed through a stdlib-doctest interface.

    Subclasses can wrap or extend xdoctest's matching by calling
    ``super().check_output(want, got, optionflags)`` to delegate the base
    comparison while adding their own pre-/post-processing.

    Note:
        This class intentionally accepts the same ``(want, got, optionflags)``
        signature as :class:`doctest.OutputChecker` so that it is a drop-in
        replacement for stdlib-shaped consumers.

    Example:
        >>> from xdoctest.stdlib_doctest import ELLIPSIS, FLOAT_CMP
        >>> output_checker = OutputChecker()
        >>> output_checker.check_output(
        >>>     'prefix ... value=1\n',
        >>>     'prefix middle value=1.0000001\n',
        >>>     ELLIPSIS | FLOAT_CMP,
        >>> )
        True
    """

    def check_output(
        self, want: str, got: str, optionflags: int
    ) -> bool:
        runstate = optionflags_to_runtime_state(optionflags)
        return checker._xdoctest_check_output(got, want, runstate)

    def output_difference(
        self,
        example: doctest.Example,
        got: str,
        optionflags: int,
    ) -> str:
        runstate = optionflags_to_runtime_state(optionflags)
        want = example.want
        ex = checker.GotWantException('got differs with doctest want', got, want)
        return ex._output_difference_xdoctest(runstate=runstate, colored=False)


__all__ = [
    'OutputChecker',
    'register_checker',
    'resolve_checker',
    'resolve_current_checker',
]

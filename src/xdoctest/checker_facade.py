"""
Stdlib-doctest-shaped façade over xdoctest's checker.

This module exposes a small public surface that lets tooling built around the
stdlib :mod:`doctest` module (most notably :mod:`pytest_doctestplus`) plug
into xdoctest's runner without having to know about xdoctest's internal
:class:`~xdoctest.directive.RuntimeState`.

Adopters typically:

1. Register their optionflags through :func:`xdoctest.register_optionflag`
   (re-exported here from :mod:`xdoctest.directive_facade`).
2. Define an :class:`OutputChecker` subclass with the standard
   ``check_output(want, got, flags)`` and (optionally)
   ``output_difference(example, got, flags)`` signatures.
3. Register the checker by name with :func:`register_checker`.
4. Select the checker for a given doctest by setting
   ``DoctestConfig['output_checker']`` to that name.
"""

from __future__ import annotations

import doctest
import types
from typing import Any, Mapping, Union

from xdoctest import checker, directive
from xdoctest.directive_facade import (
    optionflags_to_runtime_state,
    register_optionflag,
    runtime_state_to_optionflags,
)

CheckerLike = Union[doctest.OutputChecker, type]
"""
A registered checker may be either an instance or a class. Classes are
instantiated lazily by :func:`resolve_checker`.
"""

_REGISTERED_CHECKERS: dict[str, CheckerLike] = {}


def register_checker(name: str, checker_: CheckerLike) -> None:
    """
    Register an output checker under a name so it can be selected by setting
    ``DoctestConfig['output_checker']`` to that name.

    Args:
        name (str): selection key used in configs and runtime state.
        checker_: either an :class:`doctest.OutputChecker` instance or a class
            with a no-argument constructor that returns one.
    """
    _REGISTERED_CHECKERS[name] = checker_


def resolve_checker(name: str) -> doctest.OutputChecker:
    """
    Return an :class:`doctest.OutputChecker` instance for a registered name.

    Classes are instantiated each time. Instances are returned as-is.

    Raises:
        KeyError: if the name has not been registered.
    """
    if name not in _REGISTERED_CHECKERS:
        raise KeyError(
            'Unknown output checker {!r}. Known checkers are {}'.format(
                name, sorted(_REGISTERED_CHECKERS)
            )
        )
    checker_ = _REGISTERED_CHECKERS[name]
    if isinstance(checker_, doctest.OutputChecker):
        return checker_
    return checker_()


def resolve_current_checker(
    runstate: directive.RuntimeState | Mapping[str, Any] | None,
) -> doctest.OutputChecker:
    """
    Return the checker selected by the given runtime state.

    Accepts a :class:`~xdoctest.directive.RuntimeState`, a plain mapping
    (the ``_output_checker`` key is consulted), or ``None``. In all cases a
    valid checker is returned, defaulting to ``'xdoctest'``.
    """
    if isinstance(runstate, directive.RuntimeState):
        checker_name = runstate.get_output_checker()
    elif isinstance(runstate, Mapping):
        checker_name = str(runstate.get('_output_checker', 'xdoctest'))
    else:
        checker_name = 'xdoctest'
    return resolve_checker(checker_name)


class OutputChecker(doctest.OutputChecker):
    """
    Default xdoctest checker exposed through a stdlib-doctest interface.

    Subclasses can wrap or extend xdoctest's matching by calling
    ``super().check_output(want, got, flags)`` to delegate the base comparison
    while adding their own pre-/post-processing.

    Note:
        This class intentionally accepts the same ``(want, got, flags)``
        signature as :class:`doctest.OutputChecker` so that it is a drop-in
        replacement for stdlib-shaped consumers.
    """

    def check_output(self, want: str, got: str, flags: int) -> bool:
        runstate = optionflags_to_runtime_state(flags)
        return checker._xdoctest_check_output(got, want, runstate)

    def output_difference(
        self,
        example: Any,
        got: str,
        flags: int,
    ) -> str:
        runstate = optionflags_to_runtime_state(flags)
        want = getattr(example, 'want', example)
        ex = checker.GotWantException('got differs with doctest want', got, want)
        return ex._output_difference_xdoctest(runstate=runstate, colored=False)


register_checker('xdoctest', OutputChecker)


__all__ = [
    'OutputChecker',
    'register_checker',
    'resolve_checker',
    'resolve_current_checker',
    'register_optionflag',
    'runtime_state_to_optionflags',
    'optionflags_to_runtime_state',
]

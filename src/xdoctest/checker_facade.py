from __future__ import annotations

import doctest
import types
import typing

from xdoctest import checker, directive
from xdoctest.directive_facade import (
    optionflags_to_runtime_state,
    register_optionflag,
    runtime_state_to_optionflags,
)

_REGISTERED_CHECKERS: dict[
    str, doctest.OutputChecker | type[doctest.OutputChecker]
] = {}


def register_checker(
    name: str,
    checker_: doctest.OutputChecker | type[doctest.OutputChecker],
) -> None:
    _REGISTERED_CHECKERS[name] = checker_



def resolve_checker(name: str) -> doctest.OutputChecker:
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
    runstate: directive.RuntimeState | dict | None,
) -> doctest.OutputChecker:
    if isinstance(runstate, directive.RuntimeState):
        checker_name = runstate.get_output_checker()
    elif isinstance(runstate, dict):
        checker_name = str(runstate.get('_output_checker', 'xdoctest'))
    else:
        checker_name = 'xdoctest'
    return resolve_checker(checker_name)


class OutputChecker(doctest.OutputChecker):
    def check_output(
        self, want: str, got: str, optionflags: int
    ) -> bool:
        runstate = optionflags_to_runtime_state(optionflags)
        return checker._xdoctest_check_output(got, want, runstate)

    def output_difference(
        self,
        example: typing.Any,
        got: str,
        optionflags: int,
    ) -> str:
        runstate = optionflags_to_runtime_state(optionflags)
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

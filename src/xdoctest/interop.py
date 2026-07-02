"""
Public interoperability surface for third-party doctest tooling.

This module is the documented, stable contract for tools that integrate with
xdoctest's runner — pytest plugins (e.g. :mod:`pytest_doctestplus`), sphinx
extensions, or custom collectors that already speak the stdlib
:mod:`doctest` vocabulary. The surface is intentionally small:

Registration:

- :func:`register_optionflag` — register a stdlib-style optionflag by name,
  optionally bound to an xdoctest runtime-state key. Returns the same bit
  that :func:`doctest.register_optionflag` would return for that name, so
  flag bits stay consistent across both worlds. Registered flags can be
  toggled with ``# xdoctest: +MY_FLAG`` directives and are delivered to the
  active output checker via the standard ``flags`` argument.
- :func:`register_checker` — register a stdlib-shaped output checker
  (``check_output(want, got, flags)``) under a name. Select it per test via
  ``DocTest.config['output_checker'] = name``. Register an *instance* when
  the checker needs configuration (e.g. tolerances).

Conversion:

- :func:`from_examples` — build a runnable
  :class:`xdoctest.doctest_example.DocTest` from stdlib-shaped example
  objects (``source`` / ``want`` / ``lineno`` / ``options``). Line numbers
  and source content are preserved; per-example options become structured
  per-part directives.
- :func:`from_stdlib_doctest` — the same, directly from a stdlib
  :class:`doctest.DocTest`.

Helpers:

- :class:`OutputChecker` — xdoctest's native matcher behind the stdlib
  checker interface; useful as a delegation base for custom checkers.
- :func:`optionflags_to_runtime_state` / :func:`runtime_state_to_optionflags`
  — convert between stdlib optionflag ints and xdoctest's structured
  :class:`~xdoctest.directive.RuntimeState`.

Relevant ``DocTest.config`` keys (both serializable):

- ``output_checker`` (str): name of the registered checker to use.
- ``output_checker_flags`` (int): persistent checker-only optionflag bits.

The implementation modules (:mod:`xdoctest.directive_facade`,
:mod:`xdoctest.checker_facade`, :mod:`xdoctest.stdlib_compat`) are internal;
import from here instead.
"""

from xdoctest.checker_facade import (
    OutputChecker,
    register_checker,
    resolve_checker,
)
from xdoctest.directive_facade import (
    optionflags_to_runtime_state,
    register_optionflag,
    runtime_state_to_optionflags,
)
from xdoctest.stdlib_compat import from_examples, from_stdlib_doctest

__all__ = [
    'OutputChecker',
    'from_examples',
    'from_stdlib_doctest',
    'optionflags_to_runtime_state',
    'register_checker',
    'register_optionflag',
    'resolve_checker',
    'runtime_state_to_optionflags',
]

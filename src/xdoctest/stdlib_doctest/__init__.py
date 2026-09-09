r"""
Adapter API for stdlib :mod:`doctest` objects and protocols.

Tools that already produce or consume stdlib :mod:`doctest` objects can use
this package to run them through xdoctest without depending on the layout of
the private adapter modules.

Quick start
-----------

A third-party collector that already produces stdlib :mod:`doctest` objects
can register its checker and pass those objects directly to xdoctest:

Example:
    >>> import doctest
    >>> import xdoctest.stdlib_doctest as stdlib_doctest
    >>> fix = stdlib_doctest.register_optionflag('_STDLIB_DOCTEST_DOCS_FIX')
    >>> class ThirdPartyChecker(stdlib_doctest.OutputChecker):
    ...     def check_output(self, want, got, optionflags):
    ...         if optionflags & fix:
    ...             want = want.replace('L', '')
    ...             got = got.replace('L', '')
    ...         return super().check_output(want, got, optionflags)
    >>> checker_name = '_stdlib_doctest_docs_checker'
    >>> stdlib_doctest.register_checker(checker_name, ThirdPartyChecker)
    >>> example = doctest.Example(
    ...     source='print("10")\n',
    ...     want='10L\n',
    ...     lineno=0,
    ...     options={fix: True},
    ... )
    >>> converted = stdlib_doctest.from_examples(
    ...     [example],
    ...     name='third-party-example',
    ...     config={'output_checker': checker_name},
    ... )
    >>> isinstance(converted, stdlib_doctest.DocTest)
    True
    >>> converted.run(verbose=0, on_error='raise')['passed']
    True

Registration
------------

``register_optionflag``
    Register a stdlib-style option flag by name, optionally binding it to an
    xdoctest runtime-state key. The returned bit is shared with
    :func:`doctest.register_optionflag`.

``register_checker``
    Register a stdlib-shaped output checker under a configuration name.
    Select it for a test with ``DocTest.config['output_checker']``.

``resolve_checker``
    Resolve the native checker or a previously registered foreign checker.

Conversion
----------

``optionflags_to_runtime_state`` and ``runtime_state_to_optionflags``
    Convert between stdlib option-flag integers and xdoctest's structured
    runtime state.

``from_examples`` and ``from_stdlib_doctest``
    Convert stdlib-shaped examples or a complete :class:`doctest.DocTest`
    into a runnable :class:`DocTest` while preserving source locations,
    namespaces, option boundaries, and expected output.

Supporting types
----------------

``StdlibExampleLike``
    Structural protocol accepted by :func:`from_examples`.

``RuntimeState``
    Structured runtime state accepted and returned by the conversion helpers.

``DocTest``
    Runnable xdoctest object returned by the intake helpers.

``OutputChecker``
    xdoctest's native matcher exposed through the stdlib checker interface for
    composition by foreign checkers.

The overlapping registration, conversion, checker, and optionflag names remain
available at the top-level :mod:`xdoctest` namespace for compatibility. This
package is the documented home of the stdlib-doctest adapter.
"""

from xdoctest.directive import RuntimeState
from xdoctest.doctest_example import DocTest

from ._checker import OutputChecker, register_checker, resolve_checker
from ._convert import StdlibExampleLike, from_examples, from_stdlib_doctest
from ._optionflags import (
    BLANKLINE_MARKER,
    DONT_ACCEPT_BLANKLINE,
    ELLIPSIS,
    ELLIPSIS_MARKER,
    FLOAT_CMP,
    IGNORE_EXCEPTION_DETAIL,
    IGNORE_OUTPUT,
    IGNORE_WARNINGS,
    IGNORE_WHITESPACE,
    IGNORE_WANT,
    NORMALIZE_REPR,
    NORMALIZE_WHITESPACE,
    REPORT_CDIFF,
    REPORT_NDIFF,
    REPORT_UDIFF,
    SHOW_WARNINGS,
    SKIP,
    optionflags_to_runtime_state,
    register_optionflag,
    runtime_state_to_optionflags,
)

__all__ = [
    'BLANKLINE_MARKER',
    'DONT_ACCEPT_BLANKLINE',
    'DocTest',
    'ELLIPSIS',
    'ELLIPSIS_MARKER',
    'FLOAT_CMP',
    'IGNORE_EXCEPTION_DETAIL',
    'IGNORE_OUTPUT',
    'IGNORE_WARNINGS',
    'IGNORE_WHITESPACE',
    'IGNORE_WANT',
    'NORMALIZE_REPR',
    'NORMALIZE_WHITESPACE',
    'OutputChecker',
    'REPORT_CDIFF',
    'REPORT_NDIFF',
    'REPORT_UDIFF',
    'RuntimeState',
    'SHOW_WARNINGS',
    'SKIP',
    'StdlibExampleLike',
    'from_examples',
    'from_stdlib_doctest',
    'optionflags_to_runtime_state',
    'register_checker',
    'register_optionflag',
    'resolve_checker',
    'runtime_state_to_optionflags',
]

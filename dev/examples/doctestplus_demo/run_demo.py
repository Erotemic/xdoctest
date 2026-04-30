#!/usr/bin/env python
"""
Manual integration demo: run xdoctest against a module whose doctests rely on
doctestplus-style optionflags.

This demonstrates the end-to-end compatibility layer:

    xdoctest directive (`# xdoctest: +FIX`)
        -> RuntimeState
            -> stdlib-shaped optionflags ``int``
                -> doctestplus checker

The integration is bootstrapped with a single call to
``register_with_xdoctest()`` from the doctestplus submodule. No monkeypatch
of stdlib :mod:`doctest` is needed.

Run it from the repository root::

    python dev/examples/doctestplus_demo/run_demo.py

The script exits 0 on success and non-zero if any doctest fails.

It also runs the same module a second time *without* the doctestplus checker
registered, so the diff between the two runs makes the role of the checker
unmistakable: the ``FIX``-using cases must fail without doctestplus and pass
with it.

Prerequisites:

- ``xdoctest`` is importable (this repo, editable install).
- ``pytest_doctestplus`` is importable (the bundled submodule, editable
  install). The ``tpl/pytest-doctestplus`` submodule provides this module.
"""

from __future__ import annotations

import os
import sys
from typing import Any


def _ensure_paths() -> None:
    """
    Allow running directly from a checkout without installing anything.

    Adds the xdoctest source directory and the bundled doctestplus submodule
    to ``sys.path`` if they aren't already importable.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, '..', '..', '..'))

    xdoctest_src = os.path.join(repo_root, 'src')
    doctestplus_src = os.path.join(repo_root, 'tpl', 'pytest-doctestplus')

    for candidate in (xdoctest_src, doctestplus_src, here):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)


def _run(module_path: str, checker_name: str, verbose: int) -> dict[str, Any]:
    import xdoctest

    return xdoctest.doctest_module(
        module_path,
        argv=[],
        command='all',
        config={'output_checker': checker_name},
        verbose=verbose,
    )


def main() -> int:
    _ensure_paths()

    import xdoctest
    from pytest_doctestplus.xdoctest_compat import register_with_xdoctest

    print('-- doctestplus / xdoctest compatibility demo --')
    print('  xdoctest version :', xdoctest.__version__)
    print()

    import example_module  # noqa: I001

    print('# Step 1: run with the default xdoctest checker (no doctestplus).')
    print('# The FIX-using doctests are expected to FAIL because xdoctest has')
    print('# no notion of the doctestplus FIX flag.')
    print()
    baseline = _run(example_module.__file__, 'xdoctest', verbose=1)
    baseline_failed = baseline.get('n_failed', 0)
    print()
    print(f'  baseline -> failed={baseline_failed}, '
          f'passed={baseline.get("n_passed", 0)}')
    print()

    print('# Step 2: register the doctestplus checker with xdoctest and rerun.')
    print('# The FIX-using doctests should now PASS, because the doctestplus')
    print('# OutputChecker rewrites the long-integer "L" suffix.')
    print()
    register_with_xdoctest()

    integrated = _run(example_module.__file__, 'doctestplus', verbose=1)
    integrated_failed = integrated.get('n_failed', 0)
    print()
    print(f'  integrated -> failed={integrated_failed}, '
          f'passed={integrated.get("n_passed", 0)}')
    print()

    print('-- summary --')
    print(f'  baseline   failed: {baseline_failed}  '
          f'(expected > 0 to prove FIX is doctestplus-only)')
    print(f'  integrated failed: {integrated_failed}  '
          f'(expected 0 to prove the integration is wired)')

    if integrated_failed:
        print('FAIL: integrated run had failures; integration is broken.')
        return 1
    if baseline_failed == 0:
        print('FAIL: baseline run had no failures; demo no longer proves the '
              'doctestplus dependency. Adjust example_module.py.')
        return 1
    print('OK: integration demo passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

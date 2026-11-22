"""
Tests for runner-level warning policy on the stdlib-doctest intake seam.
"""

from __future__ import annotations

import doctest

import pytest

import xdoctest
from xdoctest import stdlib_compat


def _register_warning_flags():
    """
    Ensure both IGNORE_WARNINGS and SHOW_WARNINGS optionflag names exist
    in the registry. Either stdlib doctest or doctestplus might register
    them first; we just want stable ints in this test.
    """
    return (
        doctest.register_optionflag('IGNORE_WARNINGS'),
        doctest.register_optionflag('SHOW_WARNINGS'),
    )


def test_warning_policy_does_not_rewrite_source():
    """
    The user code source must be preserved verbatim; the runner-level
    policy must not wrap it in a context manager (which would shift line
    numbers and obscure failure tracebacks).
    """
    ignore_flag, _ = _register_warning_flags()
    user_source = 'import warnings; warnings.warn("noisy")\n'
    examples = [
        doctest.Example(
            source=user_source,
            want='',
            lineno=0,
            options={ignore_flag: True},
        )
    ]
    dtest = stdlib_compat.from_examples(examples, name='t')
    assert dtest.docsrc is not None
    assert user_source.strip() in dtest.docsrc
    # Source should not contain the doctestplus wrapper class.
    assert '_doctestplus_ignore_all_warnings' not in dtest.docsrc
    # And not a generic catch_warnings wrapper either.
    assert 'catch_warnings' not in dtest.docsrc


def test_ignore_warnings_silences_warning():
    ignore_flag, _ = _register_warning_flags()
    examples = [
        doctest.Example(
            source='import warnings; warnings.warn("nope")\n',
            want='',
            lineno=0,
            options={ignore_flag: True},
        )
    ]
    dtest = stdlib_compat.from_examples(examples, name='t')
    import warnings as _warnings

    with _warnings.catch_warnings(record=True) as record:
        _warnings.simplefilter('always')
        result = dtest.run(verbose=0, on_error='return')
    assert result['passed'], result
    # The warning emitted inside the doctest must not escape past the
    # per-part context manager.
    user_warnings = [w for w in record if 'nope' in str(w.message)]
    assert not user_warnings


def test_show_warnings_captures_via_stdout():
    _, show_flag = _register_warning_flags()
    examples = [
        doctest.Example(
            source='import warnings; warnings.warn("hello")\n',
            want='UserWarning: hello\n',
            lineno=0,
            options={show_flag: True},
        )
    ]
    dtest = stdlib_compat.from_examples(examples, name='t')
    result = dtest.run(verbose=0, on_error='return')
    assert result['passed'], result


def test_failure_inside_warning_context_points_at_user_code_line():
    """
    Even when a warning context wraps execution, a failure inside the user
    code must report the original file line — not a wrapper line.
    """
    ignore_flag, _ = _register_warning_flags()
    # Stdlib Example.lineno is zero-based, so lineno=7 is physical line 8.
    examples = [
        doctest.Example(
            source='import warnings; print(2)\n',
            want='1\n',
            lineno=7,
            options={ignore_flag: True},
        )
    ]
    dtest = stdlib_compat.from_examples(examples, name='t')
    result = dtest.run(verbose=0, on_error='return')
    assert result['failed']
    assert dtest.lineno == 8
    assert dtest.failed_part is not None
    assert not isinstance(dtest.failed_part, str)
    # Ensure the failed part begins at offset 0 of docsrc -> absolute line 7.
    assert dtest.failed_part.line_offset == 0


def test_no_warning_policy_uses_default_no_op_context():
    examples = [
        doctest.Example(source='print(1)\n', want='1\n', lineno=0),
    ]
    dtest = stdlib_compat.from_examples(examples, name='t')
    # Without an active runstate (or warning flags) _part_context is a no-op.
    from contextlib import nullcontext

    dtest._parse()
    assert dtest._parts
    cm = dtest._part_context(dtest._parts[0], 0)
    assert isinstance(cm, type(nullcontext()))


def test_warning_policy_is_per_part():
    """
    Warning flags on one example must not leak into other examples: the
    second part emits a warning without any flag, so it must escape to the
    ambient recorder while the first part's warning is silenced.
    """
    ignore_flag, _ = _register_warning_flags()
    examples = [
        doctest.Example(
            source='import warnings; warnings.warn("quiet")\n',
            want='',
            lineno=0,
            options={ignore_flag: True},
        ),
        doctest.Example(
            source='import warnings; warnings.warn("loud")\n',
            want='',
            lineno=2,
            options={},
        ),
    ]
    dtest = stdlib_compat.from_examples(examples, name='t')
    result = dtest.run(verbose=0, on_error='return')
    assert result['passed'], result
    # The runner records warnings that escape the parts in dtest.warn_list.
    messages = [str(w.message) for w in (dtest.warn_list or [])]
    assert not any('quiet' in m for m in messages)
    assert any('loud' in m for m in messages)

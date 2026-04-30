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
    # Example originally at file line 7; expected output mismatch.
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
    assert dtest.lineno == 7
    assert dtest.failed_part is not None
    # Ensure the failed part begins at offset 0 of docsrc -> absolute line 7.
    assert dtest.failed_part.line_offset == 0


def test_warning_policy_callback_overrides_options():
    """
    The explicit ``warning_policy`` callback wins over flag-bit detection,
    so adopters can plug in semantic policy without depending on stdlib
    optionflag conventions.
    """
    examples = [
        doctest.Example(
            source='import warnings; warnings.warn("xx")\n',
            want='',
            lineno=0,
            options={},
        )
    ]
    seen = []

    def policy(idx, ex):
        seen.append(idx)
        return 'ignore'

    dtest = stdlib_compat.from_examples(
        examples, name='t', warning_policy=policy
    )
    import warnings as _warnings

    with _warnings.catch_warnings(record=True) as record:
        _warnings.simplefilter('always')
        result = dtest.run(verbose=0, on_error='return')
    assert seen == [0]
    assert result['passed']
    assert not [w for w in record if 'xx' in str(w.message)]


def test_no_warning_policy_uses_default_no_op_context():
    examples = [
        doctest.Example(source='print(1)\n', want='1\n', lineno=0),
    ]
    dtest = stdlib_compat.from_examples(examples, name='t')
    # Default DocTest's _part_context returns nullcontext — verify by type.
    from contextlib import nullcontext

    cm = dtest._part_context(None, 0)
    assert isinstance(cm, type(nullcontext()))

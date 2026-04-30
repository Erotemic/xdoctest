"""Tests for the stdlib-doctest intake seam."""

from __future__ import annotations

import doctest

import pytest

import xdoctest
from xdoctest import stdlib_compat


def test_synthetic_example_runs_successfully():
    examples = [doctest.Example(source='print(1)\n', want='1\n', lineno=0)]
    dtest = stdlib_compat.from_examples(examples, name='t')
    result = dtest.run(verbose=0, on_error='return')
    assert result['passed']
    assert not result['failed']


def test_synthetic_example_with_failure_reports_correct_line():
    # Example at line 4 in the source file. Expecting 1, returns 2.
    examples = [doctest.Example(source='print(2)\n', want='1\n', lineno=4)]
    dtest = stdlib_compat.from_examples(
        examples, name='t', filename='/tmp/fake.py'
    )
    result = dtest.run(verbose=0, on_error='return')
    assert result['failed']
    # dtest.lineno should align with the first example's lineno so that
    # absolute file line is recovered as dtest.lineno + part.line_offset.
    assert dtest.lineno == 4
    assert dtest.failed_part is not None
    assert dtest.failed_part.line_offset == 0


def test_multiple_examples_preserve_lineno_spacing():
    examples = [
        doctest.Example(source='x = 1\n', want='', lineno=10),
        doctest.Example(source='print(x)\n', want='1\n', lineno=20),
    ]
    dtest = stdlib_compat.from_examples(examples, name='t')
    assert dtest.lineno == 10
    # Force a parse to populate _parts so we can inspect line offsets.
    dtest._parse()
    parts = dtest._parts
    assert parts is not None and len(parts) >= 2
    # Second example should be at offset 10 from the start of the docsrc,
    # so its absolute line resolves to dtest.lineno + 10 == 20.
    assert parts[-1].line_offset == 10


def test_skip_option_is_honored():
    examples = [
        doctest.Example(
            source='raise RuntimeError("should not run")\n',
            want='',
            lineno=0,
            options={doctest.SKIP: True},
        ),
        doctest.Example(source='print(2)\n', want='2\n', lineno=2),
    ]
    dtest = stdlib_compat.from_examples(examples, name='t')
    result = dtest.run(verbose=0, on_error='raise')
    assert result['passed']


def test_registered_checker_only_flag_flows_through():
    fix_flag = xdoctest.register_optionflag('FIX_INTAKE')

    seen: list[int] = []

    class Recorder(doctest.OutputChecker):
        def check_output(self, want, got, flags):
            seen.append(flags)
            return xdoctest.OutputChecker().check_output(want, got, flags)

    xdoctest.register_checker('intake_recorder', Recorder)

    examples = [doctest.Example(source='print(1)\n', want='1\n', lineno=0)]
    dtest = stdlib_compat.from_examples(
        examples,
        name='t',
        optionflags=fix_flag,
        config={'output_checker': 'intake_recorder'},
    )
    result = dtest.run(verbose=0, on_error='return')
    assert result['passed']
    assert seen
    assert seen[-1] & fix_flag


def test_stdlib_doctest_roundtrip_runs():
    stdlib_ex = doctest.Example(source='print("hi")\n', want='hi\n', lineno=2)
    stdlib_test = doctest.DocTest(
        examples=[stdlib_ex],
        globs={'__name__': '__main__'},
        name='m.f',
        filename='/tmp/m.py',
        lineno=10,
        docstring='',
    )
    dtest = stdlib_compat.from_stdlib_doctest(stdlib_test)
    result = dtest.run(verbose=0, on_error='return')
    assert result['passed']
    # Stdlib's docstring lineno (10) plus first-example offset (2) gives
    # the absolute file line. The converter sets dtest.lineno to that sum
    # so xdoctest's "dtest.lineno + part.line_offset" recovers it.
    assert dtest.lineno == 12


def test_builtin_optionflag_translates_to_runtime_state():
    # ELLIPSIS is a builtin xdoctest flag; the want uses ... to match anything.
    examples = [
        doctest.Example(
            source='print("anything happens here")\n',
            want='anything ...\n',
            lineno=0,
        )
    ]
    dtest = stdlib_compat.from_examples(
        examples, name='t', optionflags=doctest.ELLIPSIS
    )
    result = dtest.run(verbose=0, on_error='return')
    assert result['passed'], result

"""Tests for the stdlib-doctest intake seam."""

from __future__ import annotations

import copy
import doctest
from collections.abc import Iterator

import pytest

import xdoctest
from xdoctest import checker_facade, directive_facade, stdlib_compat


@pytest.fixture(autouse=True)
def isolate_interop_registries() -> Iterator[None]:
    """Restore checker and optionflag registries after each test."""
    checker_registry = checker_facade._REGISTERED_CHECKERS
    checker_snapshot = checker_registry.copy()

    runtime_flags = directive_facade._RUNTIME_FLAGS
    runtime_flags_snapshot = copy.deepcopy(runtime_flags.__dict__)

    doctest_flags = doctest.OPTIONFLAGS_BY_NAME
    doctest_flags_snapshot = doctest_flags.copy()
    doctest_counter = getattr(doctest, '_OPTION_COUNTER', None)

    try:
        yield
    finally:
        checker_registry.clear()
        checker_registry.update(checker_snapshot)

        runtime_flags.__dict__.clear()
        runtime_flags.__dict__.update(runtime_flags_snapshot)

        doctest_flags.clear()
        doctest_flags.update(doctest_flags_snapshot)
        if doctest_counter is not None:
            doctest._OPTION_COUNTER = doctest_counter


def test_synthetic_example_runs_successfully():
    examples = [doctest.Example(source='print(1)\n', want='1\n', lineno=0)]
    dtest = stdlib_compat.from_examples(examples, name='t')
    result = dtest.run(verbose=0, on_error='return')
    assert result['passed']
    assert not result['failed']


def test_synthetic_example_with_failure_reports_correct_line():
    # Stdlib Example.lineno is zero-based, so lineno=4 is physical line 5.
    examples = [doctest.Example(source='print(2)\n', want='1\n', lineno=4)]
    dtest = stdlib_compat.from_examples(
        examples, name='t', filename='/tmp/fake.py'
    )
    result = dtest.run(verbose=0, on_error='return')
    assert result['failed']
    # dtest.lineno should align with the first example's lineno so that
    # absolute file line is recovered as dtest.lineno + part.line_offset.
    assert dtest.lineno == 5
    assert dtest.failed_part is not None
    assert not isinstance(dtest.failed_part, str)
    assert dtest.failed_part.line_offset == 0


def test_multiple_examples_preserve_lineno_spacing():
    examples = [
        doctest.Example(source='x = 1\n', want='', lineno=10),
        doctest.Example(source='print(x)\n', want='1\n', lineno=20),
    ]
    dtest = stdlib_compat.from_examples(examples, name='t')
    assert dtest.lineno == 11
    # Force a parse to populate _parts so we can inspect line offsets.
    dtest._parse()
    parts = dtest._parts
    assert parts is not None and len(parts) >= 2
    # Second example should be at offset 10 from the start of the docsrc,
    # so its physical line resolves to dtest.lineno + 10 == 21.
    assert parts[-1].line_offset == 10


def test_empty_want_rejects_unexpected_stdout():
    examples = [
        doctest.Example(
            source='print("unexpected")\n',
            want='',
            lineno=0,
        )
    ]
    dtest = stdlib_compat.from_examples(examples, name='t')
    result = dtest.run(verbose=0, on_error='return')
    assert result['failed']


def test_empty_want_uses_stdlib_displayhook_semantics():
    silent = stdlib_compat.from_examples(
        [doctest.Example(source='None\n', want='', lineno=0)],
        name='silent',
    )
    assert silent.run(verbose=0, on_error='return')['passed']

    displayed = stdlib_compat.from_examples(
        [doctest.Example(source='1\n', want='', lineno=0)],
        name='displayed',
    )
    assert displayed.run(verbose=0, on_error='return')['failed']


def test_empty_want_output_cannot_satisfy_later_example():
    examples = [
        doctest.Example(source='print("a")\n', want='', lineno=0),
        doctest.Example(source='pass\n', want='a\n', lineno=1),
    ]
    dtest = stdlib_compat.from_examples(examples, name='t')
    result = dtest.run(verbose=0, on_error='return')
    assert result['failed']


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


def test_per_example_skip_preserves_execution_boundary():
    """A skipped want-less example must not skip adjacent setup code."""
    examples = [
        doctest.Example(source='x = 1\n', want='', lineno=0),
        doctest.Example(
            source='raise RuntimeError("should not run")\n',
            want='',
            lineno=1,
            options={doctest.SKIP: True},
        ),
        doctest.Example(source='print(x)\n', want='1\n', lineno=2),
    ]
    dtest = stdlib_compat.from_examples(examples, name='t')
    result = dtest.run(verbose=0, on_error='return')
    assert result['passed'], result
    assert not result['failed']
    assert dtest._parts is not None
    assert [part.source for part in dtest._parts] == [
        'x = 1',
        'raise RuntimeError("should not run")',
        'print(x)',
    ]


def test_skip_option_does_not_rewrite_source():
    """
    SKIP is attached as a structured per-part directive; the reconstructed
    source must stay byte-identical to what the user wrote.
    """
    examples = [
        doctest.Example(
            source='raise RuntimeError("should not run")\n',
            want='',
            lineno=0,
            options={doctest.SKIP: True},
        ),
    ]
    dtest = stdlib_compat.from_examples(examples, name='t')
    assert dtest.docsrc is not None
    assert 'xdoctest' not in dtest.docsrc
    assert 'SKIP' not in dtest.docsrc


def test_per_example_option_applies_to_matching_part_only():
    """
    A checker-only flag set on one example must reach the checker for that
    part but not for other parts.
    """
    part_flag = xdoctest.register_optionflag('PART_LOCAL_INTAKE')

    seen: list[int] = []

    class Recorder(doctest.OutputChecker):
        def check_output(self, want, got, optionflags):
            seen.append(optionflags)
            return xdoctest.OutputChecker().check_output(want, got, optionflags)

    xdoctest.register_checker('part_local_recorder', Recorder)

    examples = [
        doctest.Example(
            source='print(1)\n',
            want='1\n',
            lineno=0,
            options={part_flag: True},
        ),
        doctest.Example(source='print(2)\n', want='2\n', lineno=2),
    ]
    dtest = stdlib_compat.from_examples(
        examples,
        name='t',
        config={'output_checker': 'part_local_recorder'},
    )
    result = dtest.run(verbose=0, on_error='return')
    assert result['passed']
    assert len(seen) >= 2
    assert seen[0] & part_flag
    assert not (seen[-1] & part_flag)


def test_registered_checker_only_flag_flows_through():
    fix_flag = xdoctest.register_optionflag('FIX_INTAKE')

    seen: list[int] = []

    class Recorder(doctest.OutputChecker):
        def check_output(self, want, got, optionflags):
            seen.append(optionflags)
            return xdoctest.OutputChecker().check_output(want, got, optionflags)

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
    # Both stdlib values are zero-based; xdoctest stores one-based locations.
    assert dtest.lineno == 13


def test_stdlib_doctest_finder_preserves_physical_failure_line(tmp_path):
    import importlib.util

    modpath = tmp_path / 'sample_doctest_module.py'
    modpath.write_text(
        'def demo():\n'
        '    """\n'
        '    >>> print("actual")\n'
        '    expected\n'
        '    """\n'
    )
    spec = importlib.util.spec_from_file_location('sample_doctest_module', modpath)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    found = [
        test
        for test in doctest.DocTestFinder().find(module)
        if test.name.endswith('.demo')
    ]
    assert len(found) == 1
    stdlib_test = found[0]
    stdlib_example = stdlib_test.examples[0]
    physical_line = stdlib_test.lineno + stdlib_example.lineno + 1
    assert modpath.read_text().splitlines()[physical_line - 1].lstrip().startswith(
        '>>>'
    )

    dtest = stdlib_compat.from_stdlib_doctest(stdlib_test)
    result = dtest.run(verbose=0, on_error='return')
    assert result['failed']
    assert dtest.lineno == physical_line


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


def test_zero_optionflags_disable_stdlib_comparison_flags():
    ellipsis = stdlib_compat.from_examples(
        [
            doctest.Example(
                source='print("abc")\n',
                want='a...\n',
                lineno=0,
            )
        ],
        name='ellipsis',
        optionflags=0,
    )
    assert ellipsis.config['reportchoice'] == 'none'
    assert ellipsis.run(verbose=0, on_error='return')['failed']

    whitespace = stdlib_compat.from_examples(
        [
            doctest.Example(
                source='print("a  b")\n',
                want='a b\n',
                lineno=0,
            )
        ],
        name='whitespace',
        optionflags=0,
    )
    assert whitespace.run(verbose=0, on_error='return')['failed']


def test_optionflags_preserve_unrelated_runtime_config():
    examples = [doctest.Example(source='print("ok")\n', want='ok\n', lineno=0)]
    dtest = stdlib_compat.from_examples(
        examples,
        optionflags=doctest.ELLIPSIS,
        config={
            'default_runtime_state': {
                'SKIP': True,
                'ASYNC': True,
            }
        },
    )
    defaults = dtest.config['default_runtime_state']
    assert defaults['SKIP'] is True
    assert defaults['ASYNC'] is True
    assert defaults['ELLIPSIS'] is True
    assert defaults['NORMALIZE_WHITESPACE'] is False


def test_none_optionflags_preserve_configured_checker_flags():
    custom = xdoctest.register_optionflag('CONFIGURED_INTAKE_FLAG')
    examples = [doctest.Example(source='print("ok")\n', want='ok\n', lineno=0)]
    dtest = stdlib_compat.from_examples(
        examples,
        optionflags=None,
        config={'output_checker_flags': custom},
    )
    assert dtest.config['output_checker_flags'] == custom


def test_warning_flags_are_top_level_exports():
    assert xdoctest.IGNORE_WARNINGS is directive_facade.IGNORE_WARNINGS
    assert xdoctest.SHOW_WARNINGS is directive_facade.SHOW_WARNINGS



def test_local_builtin_option_overrides_global_for_foreign_checker():
    """A per-example negative builtin flag clears the configured global bit."""
    seen: list[int] = []

    class StdlibRecorder(doctest.OutputChecker):
        def check_output(self, want, got, optionflags):
            seen.append(optionflags)
            return super().check_output(want, got, optionflags)

    xdoctest.register_checker('stdlib_override_recorder', StdlibRecorder)
    examples = [
        doctest.Example(
            source='print("prefix suffix")\n',
            want='prefix ...\n',
            lineno=0,
            options={doctest.ELLIPSIS: False},
        )
    ]
    dtest = stdlib_compat.from_examples(
        examples,
        name='t',
        optionflags=doctest.ELLIPSIS,
        config={'output_checker': 'stdlib_override_recorder'},
    )
    result = dtest.run(verbose=0, on_error='return')
    assert result['failed']
    assert seen
    assert not (seen[-1] & doctest.ELLIPSIS)


def test_local_custom_option_can_mask_global_checker_flag():
    """A per-example negative custom flag masks a configured checker bit."""
    custom = xdoctest.register_optionflag('CUSTOM_INTAKE_OVERRIDE')
    seen: list[int] = []

    class Recorder(doctest.OutputChecker):
        def check_output(self, want, got, optionflags):
            seen.append(optionflags)
            return xdoctest.OutputChecker().check_output(want, got, optionflags)

    xdoctest.register_checker('custom_override_recorder', Recorder)
    examples = [
        doctest.Example(
            source='print("ok")\n',
            want='ok\n',
            lineno=0,
            options={custom: False},
        )
    ]
    dtest = stdlib_compat.from_examples(
        examples,
        name='t',
        optionflags=custom,
        config={'output_checker': 'custom_override_recorder'},
    )
    result = dtest.run(verbose=0, on_error='return')
    assert result['passed']
    assert seen
    assert not (seen[-1] & custom)

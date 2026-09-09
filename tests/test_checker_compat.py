from __future__ import annotations

import copy
import doctest
from collections.abc import Iterator
from typing import NoReturn

import pytest

import xdoctest
from xdoctest import checker, directive, doctest_example, stdlib_doctest, utils
from xdoctest.stdlib_doctest import _checker, _optionflags


@pytest.fixture(autouse=True)
def isolate_stdlib_doctest_registries() -> Iterator[None]:
    """Restore every process-global stdlib-doctest registry after each test."""
    checker_registry = _checker._REGISTERED_CHECKERS
    checker_snapshot = checker_registry.copy()

    runtime_flags = _optionflags._RUNTIME_FLAGS
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
            setattr(doctest, '_OPTION_COUNTER', doctest_counter)


def test_register_optionflag_is_stable() -> None:
    flag1 = xdoctest.register_optionflag('CUSTOM_STABLE_FLAG')
    flag2 = xdoctest.register_optionflag('CUSTOM_STABLE_FLAG')
    assert flag1 == flag2


def test_runtime_state_optionflag_roundtrip_for_builtin_flags() -> None:
    runstate = xdoctest.optionflags_to_runtime_state(
        xdoctest.FLOAT_CMP | xdoctest.ELLIPSIS
    )
    flags = xdoctest.runtime_state_to_optionflags(runstate)
    assert flags & xdoctest.FLOAT_CMP
    assert flags & xdoctest.ELLIPSIS


def register_doctestplus_like_checker() -> int:
    fix = xdoctest.register_optionflag('FIX')

    class DoctestPlusLikeChecker(doctest.OutputChecker):
        def check_output(self, want: str, got: str, optionflags: int) -> bool:
            if optionflags & fix:
                want = want.replace('L', '')
                got = got.replace('L', '')
            return xdoctest.OutputChecker().check_output(want, got, optionflags)

        def output_difference(self, example, got: str, optionflags: int) -> str:
            return 'compat-diff: ' + xdoctest.OutputChecker().output_difference(
                example, got, optionflags
            )

    xdoctest.register_checker('doctestplus_like', DoctestPlusLikeChecker)
    return fix


def test_registered_checker_can_use_doctest_style_optionflags() -> None:
    fix = register_doctestplus_like_checker()
    docsrc = utils.codeblock(
        '''
        >>> print('10')
        10L
        '''
    )
    self = doctest_example.DocTest(docsrc=docsrc)
    self.config['output_checker'] = 'doctestplus_like'
    self.config['output_checker_flags'] = fix
    result = self.run(verbose=0, on_error='raise')
    assert result['passed']


def test_registered_checker_receives_runtime_state_flags() -> None:
    seen: list[int] = []

    class FlagRecorder(doctest.OutputChecker):
        def check_output(self, want: str, got: str, optionflags: int) -> bool:
            seen.append(optionflags)
            return xdoctest.OutputChecker().check_output(want, got, optionflags)

    xdoctest.register_checker('flag_recorder', FlagRecorder)

    docsrc = utils.codeblock(
        '''
        >>> print(0.3333333333)  # xdoctest: +FLOAT_CMP
        0.333333
        '''
    )
    self = doctest_example.DocTest(docsrc=docsrc)
    self.config['output_checker'] = 'flag_recorder'
    result = self.run(verbose=0, on_error='raise')
    assert result['passed']
    assert seen
    assert seen[-1] & _optionflags.FLOAT_CMP


def test_registered_checker_output_difference_is_used() -> None:
    fix = register_doctestplus_like_checker()
    docsrc = utils.codeblock(
        '''
        >>> print('alpha')
        beta
        '''
    )
    self = doctest_example.DocTest(docsrc=docsrc)
    self.config['output_checker'] = 'doctestplus_like'
    self.config['output_checker_flags'] = fix
    result = self.run(verbose=0, on_error='return')
    assert result['failed']
    text = '\n'.join(self.repr_failure())
    assert 'compat-diff:' in text



def test_registered_optionflag_can_be_set_via_directive() -> None:
    seen: list[int] = []
    allow_bytes = xdoctest.register_optionflag('ALLOW_BYTES')

    class BytesFlagRecorder(doctest.OutputChecker):
        def check_output(self, want: str, got: str, optionflags: int) -> bool:
            seen.append(optionflags)
            return xdoctest.OutputChecker().check_output(want, got, optionflags)

    xdoctest.register_checker('bytes_flag_recorder', BytesFlagRecorder)

    docsrc = utils.codeblock(
        '''
        >>> print('alpha')  # xdoctest: +ALLOW_BYTES
        alpha
        >>> print('beta')
        beta
        '''
    )
    self = doctest_example.DocTest(docsrc=docsrc)
    self.config['output_checker'] = 'bytes_flag_recorder'
    result = self.run(verbose=0, on_error='raise')
    assert result['passed']
    assert len(seen) >= 2
    assert seen[0] & allow_bytes
    assert not (seen[-1] & allow_bytes)


def test_resolve_current_checker_honors_mapping_state() -> None:
    class MappingChecker(doctest.OutputChecker):
        pass

    xdoctest.register_checker('mapping_checker', MappingChecker)
    resolved = _checker.resolve_current_checker(
        {'_output_checker': 'mapping_checker'}
    )
    assert isinstance(resolved, MappingChecker)


def test_registered_optionflag_inline_reaches_checker() -> None:
    seen: list[int] = []
    fix_inline = xdoctest.register_optionflag('FIX_INLINE')

    class InlineRecorder(doctest.OutputChecker):
        def check_output(self, want: str, got: str, optionflags: int) -> bool:
            seen.append(optionflags)
            return xdoctest.OutputChecker().check_output(want, got, optionflags)

    xdoctest.register_checker('inline_flag_recorder', InlineRecorder)

    docsrc = utils.codeblock(
        """
        >>> print('alpha')  # xdoctest: +FIX_INLINE
        alpha
        """
    )
    self = doctest_example.DocTest(docsrc=docsrc)
    self.config['output_checker'] = 'inline_flag_recorder'
    result = self.run(verbose=0, on_error='raise')
    assert result['passed']
    assert seen
    assert seen[-1] & fix_inline



def test_registered_optionflag_inline_clears_after_part() -> None:
    seen: list[int] = []
    fix_inline_once = xdoctest.register_optionflag('FIX_INLINE_ONCE')

    class InlineOnceRecorder(doctest.OutputChecker):
        def check_output(self, want: str, got: str, optionflags: int) -> bool:
            seen.append(optionflags)
            return xdoctest.OutputChecker().check_output(want, got, optionflags)

    xdoctest.register_checker('inline_once_recorder', InlineOnceRecorder)

    docsrc = utils.codeblock(
        """
        >>> print('alpha')  # xdoctest: +FIX_INLINE_ONCE
        alpha
        >>> print('beta')
        beta
        """
    )
    self = doctest_example.DocTest(docsrc=docsrc)
    self.config['output_checker'] = 'inline_once_recorder'
    result = self.run(verbose=0, on_error='raise')
    assert result['passed']
    assert len(seen) >= 2
    assert seen[0] & fix_inline_once
    assert not (seen[1] & fix_inline_once)



def test_registered_optionflag_block_persists_until_disabled() -> None:
    seen: list[int] = []
    fix_block = xdoctest.register_optionflag('FIX_BLOCK')

    class BlockRecorder(doctest.OutputChecker):
        def check_output(self, want: str, got: str, optionflags: int) -> bool:
            seen.append(optionflags)
            return xdoctest.OutputChecker().check_output(want, got, optionflags)

    xdoctest.register_checker('block_flag_recorder', BlockRecorder)

    docsrc = utils.codeblock(
        """
        >>> # xdoctest: +FIX_BLOCK
        >>> print('alpha')
        alpha
        >>> print('beta')
        beta
        >>> # xdoctest: -FIX_BLOCK
        >>> print('gamma')
        gamma
        """
    )
    self = doctest_example.DocTest(docsrc=docsrc)
    self.config['output_checker'] = 'block_flag_recorder'
    result = self.run(verbose=0, on_error='raise')
    assert result['passed']
    assert len(seen) >= 3
    assert seen[0] & fix_block
    assert seen[1] & fix_block
    assert not (seen[2] & fix_block)



def test_registered_optionflag_negative_block_clears_correctly() -> None:
    seen: list[int] = []
    fix_toggle = xdoctest.register_optionflag('FIX_TOGGLE')

    class ToggleRecorder(doctest.OutputChecker):
        def check_output(self, want: str, got: str, optionflags: int) -> bool:
            seen.append(optionflags)
            return xdoctest.OutputChecker().check_output(want, got, optionflags)

    xdoctest.register_checker('toggle_flag_recorder', ToggleRecorder)

    docsrc = utils.codeblock(
        """
        >>> # xdoctest: +FIX_TOGGLE
        >>> print('alpha')
        alpha
        >>> # xdoctest: -FIX_TOGGLE
        >>> print('beta')
        beta
        >>> # xdoctest: +FIX_TOGGLE
        >>> print('gamma')
        gamma
        """
    )
    self = doctest_example.DocTest(docsrc=docsrc)
    self.config['output_checker'] = 'toggle_flag_recorder'
    result = self.run(verbose=0, on_error='raise')
    assert result['passed']
    assert len(seen) >= 3
    assert seen[0] & fix_toggle
    assert not (seen[1] & fix_toggle)
    assert seen[2] & fix_toggle



def test_custom_checker_selected_by_name_receives_registered_directive_flags() -> None:
    seen: list[int] = []
    fix_named = xdoctest.register_optionflag('FIX_SELECTED_BY_NAME')

    class NamedRecorder(doctest.OutputChecker):
        def check_output(self, want: str, got: str, optionflags: int) -> bool:
            seen.append(optionflags)
            return xdoctest.OutputChecker().check_output(want, got, optionflags)

    xdoctest.register_checker('named_flag_recorder', NamedRecorder)

    docsrc = utils.codeblock(
        """
        >>> print('alpha')  # xdoctest: +FIX_SELECTED_BY_NAME
        alpha
        """
    )
    self = doctest_example.DocTest(docsrc=docsrc)
    self.config['output_checker'] = 'named_flag_recorder'
    result = self.run(verbose=0, on_error='raise')
    assert result['passed']
    assert seen
    assert seen[-1] & fix_named



def test_end_to_end_registered_checker_flag_works_via_directive() -> None:
    fix_end_to_end = xdoctest.register_optionflag('FIX_END_TO_END')

    class FixDirectiveChecker(doctest.OutputChecker):
        def check_output(self, want: str, got: str, optionflags: int) -> bool:
            if optionflags & fix_end_to_end:
                want = want.replace('L', '')
                got = got.replace('L', '')
            return xdoctest.OutputChecker().check_output(want, got, optionflags)

    xdoctest.register_checker('fix_directive_checker', FixDirectiveChecker)

    docsrc = utils.codeblock(
        """
        >>> print('10')  # xdoctest: +FIX_END_TO_END
        10L
        >>> print('20')
        20
        """
    )
    self = doctest_example.DocTest(docsrc=docsrc)
    self.config['output_checker'] = 'fix_directive_checker'
    result = self.run(verbose=0, on_error='raise')
    assert result['passed']


def test_runtime_bound_flag_can_be_cleared_after_conversion() -> None:
    runstate = xdoctest.optionflags_to_runtime_state(xdoctest.FLOAT_CMP)
    assert runstate['FLOAT_CMP']

    runstate['FLOAT_CMP'] = False
    flags = xdoctest.runtime_state_to_optionflags(runstate)
    assert not (flags & xdoctest.FLOAT_CMP)


def test_configured_builtin_flag_can_be_disabled_locally() -> None:
    seen: list[int] = []

    class FlagRecorder(doctest.OutputChecker):
        def check_output(self, want: str, got: str, optionflags: int) -> bool:
            seen.append(optionflags)
            return super().check_output(want, got, optionflags)

    xdoctest.register_checker('builtin_override_recorder', FlagRecorder)
    docsrc = utils.codeblock(
        """
        >>> print('1.0000001')  # xdoctest: -FLOAT_CMP
        1
        """
    )
    dtest = doctest_example.DocTest(docsrc=docsrc)
    dtest.config['output_checker'] = 'builtin_override_recorder'
    dtest.config['output_checker_flags'] = xdoctest.FLOAT_CMP

    result = dtest.run(verbose=0, on_error='return')

    assert result['failed']
    assert seen
    assert not (seen[-1] & xdoctest.FLOAT_CMP)


def test_inline_negative_custom_flag_masks_global_flag_for_one_part() -> None:
    seen: list[int] = []
    custom_flag = xdoctest.register_optionflag('CUSTOM_INLINE_MASK')

    class FlagRecorder(doctest.OutputChecker):
        def check_output(self, want: str, got: str, optionflags: int) -> bool:
            seen.append(optionflags)
            return xdoctest.OutputChecker().check_output(want, got, optionflags)

    xdoctest.register_checker('custom_mask_recorder', FlagRecorder)
    docsrc = utils.codeblock(
        """
        >>> # xdoctest: +CUSTOM_INLINE_MASK
        >>> print('first')
        first
        >>> print('second')  # xdoctest: -CUSTOM_INLINE_MASK
        second
        >>> print('third')
        third
        """
    )
    dtest = doctest_example.DocTest(docsrc=docsrc)
    dtest.config['output_checker'] = 'custom_mask_recorder'

    result = dtest.run(verbose=0, on_error='raise')

    assert result['passed']
    assert len(seen) == 3
    assert seen[0] & custom_flag
    assert not (seen[1] & custom_flag)
    assert seen[2] & custom_flag


def test_output_checker_honors_ignore_output() -> None:
    output_checker = xdoctest.OutputChecker()
    assert output_checker.check_output(
        'expected',
        'actual',
        xdoctest.IGNORE_OUTPUT,
    )



def test_native_checker_name_is_reserved() -> None:
    with pytest.raises(ValueError, match='reserved'):
        _checker.register_checker('xdoctest', doctest.OutputChecker)

    assert isinstance(
        _checker.resolve_checker('xdoctest'),
        _checker.OutputChecker,
    )
    assert 'xdoctest' not in _checker._REGISTERED_CHECKERS


def test_registered_class_retains_factory_semantics() -> None:
    class Counting(doctest.OutputChecker):
        instances = 0

        def __init__(self) -> None:
            Counting.instances += 1

    _checker.register_checker('counting_factory', Counting)
    first = _checker.resolve_checker('counting_factory')
    second = _checker.resolve_checker('counting_factory')
    assert first is not second
    assert Counting.instances == 2

    replacement = doctest.OutputChecker()
    _checker.register_checker('counting_factory', replacement)
    assert _checker.resolve_checker('counting_factory') is replacement


def test_registered_class_is_cached_per_runtime_state() -> None:
    class Counting(doctest.OutputChecker):
        instances = 0

        def __init__(self) -> None:
            Counting.instances += 1

    _checker.register_checker('counting_per_run', Counting)

    first_run = directive.RuntimeState()
    first_run.set_output_checker('counting_per_run')
    first = _checker.resolve_current_checker(first_run)
    assert _checker.resolve_current_checker(first_run) is first
    assert Counting.instances == 1

    second_run = directive.RuntimeState()
    second_run.set_output_checker('counting_per_run')
    second = _checker.resolve_current_checker(second_run)
    assert second is not first
    assert Counting.instances == 2

    # Even re-registering the same class creates a new registry generation and
    # invalidates a previously cached checker within the bounded run state.
    _checker.register_checker('counting_per_run', Counting)
    third = _checker.resolve_current_checker(first_run)
    assert third is not first
    assert Counting.instances == 3


def test_matching_and_difference_share_one_per_run_checker() -> None:
    class Stateful(doctest.OutputChecker):
        instances = 0

        def __init__(self) -> None:
            Stateful.instances += 1
            self.checked = False

        def check_output(self, want: str, got: str, optionflags: int) -> bool:
            self.checked = True
            return False

        def output_difference(
            self,
            example: doctest.Example,
            got: str,
            optionflags: int,
        ) -> str:
            assert self.checked
            return 'same per-run checker'

    _checker.register_checker('stateful_per_run', Stateful)
    runstate = directive.RuntimeState()
    runstate.set_output_checker('stateful_per_run')

    assert not checker.check_output('actual', 'expected', runstate)
    difference = checker.GotWantException(
        'different', 'actual', 'expected'
    ).output_difference(runstate, colored=False)
    assert difference == 'same per-run checker'
    assert Stateful.instances == 1


def test_native_check_bypasses_stdlib_doctest_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The native RuntimeState path must not pack or resolve adapter state."""

    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError('native path crossed the stdlib-doctest boundary')

    monkeypatch.setattr(
        _optionflags, 'runtime_state_to_optionflags', forbidden
    )
    monkeypatch.setattr(_checker, 'resolve_checker', forbidden)

    runstate = directive.RuntimeState()
    assert checker.check_output('1\n', '1\n', runstate)
    assert not checker.check_output('1\n', '2\n', runstate)


def test_sparse_mapping_is_normalized_before_native_matching() -> None:
    sparse = {'_output_checker': 'xdoctest'}
    assert not checker.check_output('actual', 'expected', sparse)

    difference = checker.GotWantException(
        'different', 'actual', 'expected'
    ).output_difference(sparse, colored=False)
    assert 'Expected:' in difference
    assert 'Got:' in difference


def test_public_stdlib_doctest_namespace_contract() -> None:
    from xdoctest import doctest_example, stdlib_doctest
    from xdoctest.stdlib_doctest import _convert

    expected = [
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
    assert stdlib_doctest.__all__ == expected

    # The package preserves every overlapping API currently re-exported
    # from the top-level xdoctest namespace.
    assert stdlib_doctest.OutputChecker is xdoctest.OutputChecker
    assert stdlib_doctest.register_checker is xdoctest.register_checker
    assert stdlib_doctest.resolve_checker is xdoctest.resolve_checker
    assert stdlib_doctest.register_optionflag is xdoctest.register_optionflag
    assert (
        stdlib_doctest.optionflags_to_runtime_state
        is xdoctest.optionflags_to_runtime_state
    )
    assert (
        stdlib_doctest.runtime_state_to_optionflags
        is xdoctest.runtime_state_to_optionflags
    )

    # Type-aware users can stay entirely within the public package.
    assert stdlib_doctest.RuntimeState is directive.RuntimeState
    assert stdlib_doctest.DocTest is doctest_example.DocTest
    assert stdlib_doctest.StdlibExampleLike is _convert.StdlibExampleLike
    assert stdlib_doctest.from_examples is _convert.from_examples
    assert (
        stdlib_doctest.from_stdlib_doctest
        is _convert.from_stdlib_doctest
    )


def test_public_stdlib_doctest_preserves_stdlib_behavior() -> None:
    """The public package accepts and executes real stdlib objects."""
    from xdoctest import stdlib_doctest

    example = doctest.Example(
        source='print("prefix suffix")\n',
        want='prefix ...\n',
        lineno=3,
        options={doctest.ELLIPSIS: True},
    )
    stdlib_test = doctest.DocTest(
        examples=[example],
        globs={'__name__': '__main__'},
        name='package.demo',
        filename='demo.py',
        lineno=10,
        docstring='',
    )

    stdlib_result = doctest.DocTestRunner().run(
        stdlib_test,
        out=lambda text: None,
        clear_globs=False,
    )
    assert stdlib_result.failed == 0
    assert stdlib_result.attempted == 1

    stdlib_doctest.register_checker(
        'public_stdlib_output_checker', doctest.OutputChecker
    )
    converted = stdlib_doctest.from_stdlib_doctest(
        stdlib_test,
        config={'output_checker': 'public_stdlib_output_checker'},
    )
    assert isinstance(converted, stdlib_doctest.DocTest)
    assert converted.callname == stdlib_test.name
    assert converted.lineno == 14
    assert converted.run(verbose=0, on_error='return')['passed']


def test_public_stdlib_doctest_checker_protocol_end_to_end() -> None:
    """Package registration and intake obey the stdlib checker protocol."""
    from xdoctest import stdlib_doctest

    fix_flag = stdlib_doctest.register_optionflag('PUBLIC_STDLIB_DOCTEST_FIX')
    seen: list[int] = []

    class PublicStdlibDoctestChecker(stdlib_doctest.OutputChecker):
        def check_output(
            self, want: str, got: str, optionflags: int
        ) -> bool:
            seen.append(optionflags)
            if optionflags & fix_flag:
                want = want.replace('L', '')
                got = got.replace('L', '')
            return super().check_output(want, got, optionflags)

    stdlib_doctest.register_checker(
        'public_stdlib_doctest_checker', PublicStdlibDoctestChecker
    )
    examples = [
        doctest.Example(
            source='print("10")\n',
            want='10L\n',
            lineno=0,
            options={fix_flag: True},
        )
    ]
    converted = stdlib_doctest.from_examples(
        examples,
        name='public-stdlib-doctest',
        config={'output_checker': 'public_stdlib_doctest_checker'},
    )

    assert isinstance(converted, stdlib_doctest.DocTest)
    assert converted.run(verbose=0, on_error='return')['passed']
    assert seen
    assert seen[-1] & fix_flag

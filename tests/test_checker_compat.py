from __future__ import annotations

import copy
import doctest
from collections.abc import Iterator
from typing import NoReturn

import pytest

import xdoctest
from xdoctest import checker, checker_facade, directive, doctest_example, utils
from xdoctest import directive_facade


@pytest.fixture(autouse=True)
def isolate_interop_registries() -> Iterator[None]:
    """Restore every process-global interop registry after each test."""
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
    assert seen[-1] & directive_facade.FLOAT_CMP


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
    resolved = xdoctest.checker_facade.resolve_current_checker(
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
        checker_facade.register_checker('xdoctest', doctest.OutputChecker)

    assert isinstance(
        checker_facade.resolve_checker('xdoctest'),
        checker_facade.OutputChecker,
    )
    assert 'xdoctest' not in checker_facade._REGISTERED_CHECKERS


def test_registered_class_retains_factory_semantics() -> None:
    class Counting(doctest.OutputChecker):
        instances = 0

        def __init__(self) -> None:
            Counting.instances += 1

    checker_facade.register_checker('counting_factory', Counting)
    first = checker_facade.resolve_checker('counting_factory')
    second = checker_facade.resolve_checker('counting_factory')
    assert first is not second
    assert Counting.instances == 2

    replacement = doctest.OutputChecker()
    checker_facade.register_checker('counting_factory', replacement)
    assert checker_facade.resolve_checker('counting_factory') is replacement


def test_registered_class_is_cached_per_runtime_state() -> None:
    class Counting(doctest.OutputChecker):
        instances = 0

        def __init__(self) -> None:
            Counting.instances += 1

    checker_facade.register_checker('counting_per_run', Counting)

    first_run = directive.RuntimeState()
    first_run.set_output_checker('counting_per_run')
    first = checker_facade.resolve_current_checker(first_run)
    assert checker_facade.resolve_current_checker(first_run) is first
    assert Counting.instances == 1

    second_run = directive.RuntimeState()
    second_run.set_output_checker('counting_per_run')
    second = checker_facade.resolve_current_checker(second_run)
    assert second is not first
    assert Counting.instances == 2

    # Even re-registering the same class creates a new registry generation and
    # invalidates a previously cached checker within the bounded run state.
    checker_facade.register_checker('counting_per_run', Counting)
    third = checker_facade.resolve_current_checker(first_run)
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

    checker_facade.register_checker('stateful_per_run', Stateful)
    runstate = directive.RuntimeState()
    runstate.set_output_checker('stateful_per_run')

    assert not checker.check_output('actual', 'expected', runstate)
    difference = checker.GotWantException(
        'different', 'actual', 'expected'
    ).output_difference(runstate, colored=False)
    assert difference == 'same per-run checker'
    assert Stateful.instances == 1


def test_native_check_bypasses_the_interop_facade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The native RuntimeState path must not pack or resolve facade state."""

    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError('native path crossed the interop boundary')

    monkeypatch.setattr(
        checker_facade, 'runtime_state_to_optionflags', forbidden
    )
    monkeypatch.setattr(checker_facade, 'resolve_checker', forbidden)

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

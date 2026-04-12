from xdoctest import checker, directive

# from xdoctest import utils


def test_visible_lines() -> None:
    """
    pytest tests/test_checker.py
    """
    got = 'this is invisible\ronly this is visible'
    print(got)
    want = 'only this is visible'
    assert checker.check_output(got, want)


def test_visible_lines_explicit() -> None:
    """
    pytest tests/test_checker.py
    """
    got = 'invisible\rIS-visible'
    want = 'invisible\rIS-visible'
    # The got-want checker is quite permissive.
    # Use asserts for non-permissive tests.
    assert checker.check_output(got, want)


def test_blankline_accept() -> None:
    """
    pytest tests/test_checker.py
    """
    # Check that blankline is normalized away
    runstate = directive.RuntimeState({'DONT_ACCEPT_BLANKLINE': False})
    got = 'foo\n\nbar'
    want = 'foo\n<BLANKLINE>\nbar'
    assert checker.check_output(got, want, runstate)


def test_blankline_failcase() -> None:
    # Check that blankline is not normalizd in a "got" statement
    runstate = directive.RuntimeState({'DONT_ACCEPT_BLANKLINE': False})
    got = 'foo\n<BLANKLINE>\nbar'
    want = 'foo\n\nbar'
    assert not checker.check_output(got, want, runstate)


def test_blankline_not_accept() -> None:
    # Check that blankline is not normalized away when
    # DONT_ACCEPT_BLANKLINE is on
    runstate = directive.RuntimeState({'DONT_ACCEPT_BLANKLINE': True})
    got = 'foo\n\nbar'
    want = 'foo\n<BLANKLINE>\nbar'
    assert not checker.check_output(got, want, runstate)


def test_float_cmp_simple_pass() -> None:
    runstate = directive.RuntimeState({'FLOAT_CMP': True})
    got = '0.3333333333333333'
    want = '0.333333'
    assert checker.check_output(got, want, runstate)


def test_float_cmp_simple_mismatch_fail() -> None:
    runstate = directive.RuntimeState({'FLOAT_CMP': True})
    got = '1.0'
    want = '1.1'
    assert not checker.check_output(got, want, runstate)


def test_float_cmp_text_with_numbers_pass() -> None:
    runstate = directive.RuntimeState({'FLOAT_CMP': True})
    got = 'best=0.3333333333333333 ave=0.6666666666666666'
    want = 'best=0.333333 ave=0.666666'
    assert checker.check_output(got, want, runstate)


def test_float_cmp_ellipsis_composes() -> None:
    runstate = directive.RuntimeState({'FLOAT_CMP': True, 'ELLIPSIS': True})
    got = 'prefix best=0.3333333333 s ave=0.6666666666 suffix'
    want = 'prefix best=... s ave=0.666666 suffix'
    assert checker.check_output(got, want, runstate)


def test_float_cmp_does_not_enable_ellipsis_by_itself() -> None:
    runstate = directive.RuntimeState({'FLOAT_CMP': True, 'ELLIPSIS': False})
    got = 'prefix best=0.3333333333 suffix'
    want = 'prefix best=... suffix'
    assert not checker.check_output(got, want, runstate)


def test_float_cmp_special_values_and_multiple_numbers() -> None:
    runstate = directive.RuntimeState({'FLOAT_CMP': True})
    got = 'value=NaN upper=INF lower=-Infinity pair=1.0,2.0000000001'
    want = 'value=nan upper=inf lower=-inf pair=1,2'
    assert checker.check_output(got, want, runstate)

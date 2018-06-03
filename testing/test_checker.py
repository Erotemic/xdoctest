from xdoctest import checker
from xdoctest import directive
# from xdoctest import utils


def test_visible_lines():
    """
    pytest testing/test_checker.py
    """
    got = 'this is invisible\ronly this is visible'
    print(got)
    want = 'only this is visible'
    assert checker.check_output(got, want)


def test_visible_lines_explicit():
    """
    pytest testing/test_checker.py
    """
    got = 'invisible\rIS-visible'
    want = 'invisible\rIS-visible'
    # The got-want checker is quite permissive.
    # Use asserts for non-permissive tests.
    assert checker.check_output(got, want)


def test_blankline_accept():
    """
    pytest testing/test_checker.py
    """
    # Check that blankline is normalized away
    runstate = directive.RuntimeState({'DONT_ACCEPT_BLANKLINE': False})
    got = 'foo\n\nbar'
    want = 'foo\n<BLANKLINE>\nbar'
    assert checker.check_output(got, want, runstate)


def test_blankline_failcase():
    # Check that blankline is not normalizd in a "got" statement
    runstate = directive.RuntimeState({'DONT_ACCEPT_BLANKLINE': False})
    got = 'foo\n<BLANKLINE>\nbar'
    want = 'foo\n\nbar'
    assert not checker.check_output(got, want, runstate)


def test_blankline_not_accept():
    # Check that blankline is not normalized away when
    # DONT_ACCEPT_BLANKLINE is on
    runstate = directive.RuntimeState({'DONT_ACCEPT_BLANKLINE': True})
    got = 'foo\n\nbar'
    want = 'foo\n<BLANKLINE>\nbar'
    assert not checker.check_output(got, want, runstate)

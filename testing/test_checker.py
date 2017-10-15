from xdoctest import checker
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

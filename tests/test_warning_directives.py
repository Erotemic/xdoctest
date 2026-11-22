"""
Tests for the native IGNORE_WARNINGS / SHOW_WARNINGS runtime directives.

These directives apply warning policy at the runner level: the part's source
is never rewritten, so failure line numbers always point at user code.
"""

from xdoctest import doctest_example, utils


def _run(docsrc):
    dtest = doctest_example.DocTest(docsrc=docsrc)
    return dtest, dtest.run(on_error='return', verbose=0)


def test_ignore_warnings_inline():
    """
    An inline +IGNORE_WARNINGS silences a warning that would otherwise be
    escalated to an error by the ambient filter.
    """
    string = utils.codeblock(
        """
        >>> import warnings
        >>> warnings.simplefilter('error')
        >>> warnings.warn('boo')  # xdoctest: +IGNORE_WARNINGS
        >>> print('done')
        done
        """
    )
    dtest, result = _run(string)
    assert result['passed']


def test_escalated_warning_fails_without_directive():
    string = utils.codeblock(
        """
        >>> import warnings
        >>> warnings.simplefilter('error')
        >>> warnings.warn('boo')
        >>> print('done')
        done
        """
    )
    dtest, result = _run(string)
    assert result['failed']


def test_show_warnings_inline():
    """
    +SHOW_WARNINGS prints captured warnings as ``Category: message`` lines
    that participate in got/want matching.
    """
    string = utils.codeblock(
        """
        >>> import warnings
        >>> warnings.warn('boo')  # xdoctest: +SHOW_WARNINGS
        UserWarning: boo
        """
    )
    dtest, result = _run(string)
    assert result['passed']


def test_warning_not_shown_without_directive():
    string = utils.codeblock(
        """
        >>> import warnings
        >>> warnings.warn('boo')
        UserWarning: boo
        """
    )
    dtest, result = _run(string)
    assert result['failed']


def test_ignore_warnings_block_scope():
    """
    A block-form directive persists for subsequent parts until disabled.
    """
    string = utils.codeblock(
        """
        >>> import warnings
        >>> warnings.simplefilter('error')
        >>> print('setup')
        setup
        >>> # xdoctest: +IGNORE_WARNINGS
        >>> warnings.warn('one')
        >>> print('a')
        a
        >>> warnings.warn('two')
        >>> print('b')
        b
        """
    )
    dtest, result = _run(string)
    assert result['passed']


def test_ignore_takes_precedence_over_show():
    string = utils.codeblock(
        """
        >>> import warnings
        >>> # xdoctest: +IGNORE_WARNINGS, +SHOW_WARNINGS
        >>> warnings.warn('boo')
        >>> print('done')
        done
        """
    )
    dtest, result = _run(string)
    assert result['passed']


def test_show_warnings_preserves_source_and_lineno():
    """
    A failing part under SHOW_WARNINGS reports the original user source, not
    wrapper code, and the failing part's line offset matches the user line.
    """
    string = utils.codeblock(
        """
        >>> import warnings
        >>> warnings.warn('boo')  # xdoctest: +SHOW_WARNINGS
        UserWarning: not-what-was-warned
        """
    )
    dtest, result = _run(string)
    assert result['failed']
    failed_part = dtest.failed_part
    assert 'with ' not in failed_part.source
    assert "warnings.warn('boo')" in failed_part.source
    # Got/want failures point at the want line: the part starts at offset 1
    # and its single want line is at offset 2.
    assert dtest.failed_line_offset() == 2

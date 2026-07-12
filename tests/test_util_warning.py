"""Focused tests for warning context-manager utilities."""

import warnings

import pytest

from xdoctest.utils import IgnoreWarnings, ShowWarnings


def test_ignore_warnings_restores_ambient_filter():
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        with IgnoreWarnings():
            warnings.warn('hidden')
        with pytest.raises(UserWarning, match='visible again'):
            warnings.warn('visible again')


def test_ignore_warnings_context_is_reusable():
    context = IgnoreWarnings()
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        with context:
            warnings.warn('hidden once')
        with context:
            warnings.warn('hidden twice')


def test_show_warnings_prints_category_and_message(capsys):
    class CustomWarning(Warning):
        pass

    with ShowWarnings() as context:
        warnings.warn('first', CustomWarning)
        warnings.warn('second', UserWarning)

    captured = capsys.readouterr()
    assert captured.out == 'CustomWarning: first\nUserWarning: second\n'
    assert [str(item.message) for item in context.captured] == [
        'first',
        'second',
    ]


def test_show_warnings_restores_ambient_filter(capsys):
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        with ShowWarnings():
            warnings.warn('shown')
        with pytest.raises(UserWarning, match='raised again'):
            warnings.warn('raised again')

    assert capsys.readouterr().out == 'UserWarning: shown\n'


def test_show_warnings_does_not_swallow_or_print_on_exception(capsys):
    with pytest.raises(RuntimeError, match='body failed'):
        with ShowWarnings():
            warnings.warn('not printed after failure')
            raise RuntimeError('body failed')

    assert capsys.readouterr().out == ''


def test_warning_context_rejects_active_reentry():
    ignore = IgnoreWarnings()
    with ignore:
        with pytest.raises(RuntimeError, match='re-entered'):
            ignore.__enter__()

    show = ShowWarnings()
    with show:
        with pytest.raises(RuntimeError, match='re-entered'):
            show.__enter__()

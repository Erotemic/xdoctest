"""Tests for pickling objects defined in an executing doctest."""

import sys
from pathlib import Path

import pytest

from xdoctest.doctest_example import DocTest
from xdoctest.utils import codeblock


def _sandbox_names() -> set[str]:
    return {name for name in sys.modules if name.startswith('_xdoctest_sandbox_')}


@pytest.mark.parametrize('with_module', [False, True])
def test_doctest_classes_and_functions_are_pickleable(
    tmp_path: Path, with_module: bool
) -> None:
    """A doctest acts as a module while it is executing, without module leaks."""
    modpath = None
    if with_module:
        modpath = str(tmp_path / 'pickle_owner.py')
        (tmp_path / 'pickle_owner.py').write_text('"""Owner module."""\n')

    docsrc = codeblock(
        '''
        >>> import pickle
        >>> import sys
        >>> def helper(value):
        >>>     return value + 1
        >>> def passthrough(cls):
        >>>     return cls
        >>> @passthrough
        >>> class LocalModel:
        >>>     def __init__(self, value):
        >>>         self.value = value
        >>> model = LocalModel(3)
        >>> loaded = pickle.loads(pickle.dumps(model))
        >>> assert type(loaded) is LocalModel
        >>> assert loaded.value == 3
        >>> assert pickle.loads(pickle.dumps(helper)) is helper
        >>> assert sys.modules[LocalModel.__module__].LocalModel is LocalModel
        '''
    )
    dtest = DocTest(
        docsrc=docsrc, modpath=modpath, callname='__doc__', mode='native'
    )
    before = _sandbox_names()
    result = dtest.run(verbose=0, on_error='return')
    assert result['passed'], '\n'.join(dtest.repr_failure())
    assert _sandbox_names() == before
    if with_module:
        assert not hasattr(dtest.module, 'LocalModel')


def test_pickle_namespace_cleaned_on_exception() -> None:
    """A failed doctest must not leave its temporary module registered."""
    docsrc = codeblock(
        '''
        >>> class LocalModel:
        >>>     pass
        >>> import sys
        >>> assert sys.modules[LocalModel.__module__].LocalModel is LocalModel
        >>> raise ValueError('expected failure')
        '''
    )
    dtest = DocTest(docsrc=docsrc, mode='native')
    before = _sandbox_names()
    with pytest.raises(ValueError, match='expected failure'):
        dtest.run(verbose=0, on_error='raise')
    assert _sandbox_names() == before

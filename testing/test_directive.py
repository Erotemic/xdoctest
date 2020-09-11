# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from xdoctest import doctest_example
from xdoctest import utils


def test_inline_skip_directive():
    """
    pytest testing/test_directive.py::test_inline_skip_directive
    """
    string = utils.codeblock(
        '''
        >>> x = 0
        >>> assert False, 'should be skipped'  # doctest: +SKIP
        >>> y = 0
        ''')
    self = doctest_example.DocTest(docsrc=string)
    result = self.run(on_error='raise')
    # TODO: ensure that lines after the inline are run
    assert result['passed']


def test_block_skip_directive():
    """
    pytest testing/test_directive.py::test_block_skip_directive
    """
    string = utils.codeblock(
        '''
        >>> x = 0
        >>> # doctest: +SKIP
        >>> assert False, 'should be skipped'
        ''')
    self = doctest_example.DocTest(docsrc=string)
    result = self.run(on_error='raise')
    assert result['passed']


def test_multi_requires_directive():
    """
    Test semi-complex case with multiple requirements in a single line

    xdoctest ~/code/xdoctest/testing/test_directive.py test_multi_requires_directive
    """
    string = utils.codeblock(
        '''
        >>> x = 0
        >>> print('not-skipped')
        >>> # doctest: +REQUIRES(env:NOT_EXIST, --show, module:xdoctest)
        >>> print('is-skipped')
        >>> assert False, 'should be skipped'
        >>> # doctest: -REQUIRES(env:NOT_EXIST, module:xdoctest)
        >>> print('is-skipped')
        >>> assert False, 'should be skipped'
        >>> # doctest: +REQUIRES(env:NOT_EXIST, --show, module:xdoctest)
        >>> print('is-skipped')
        >>> assert False, 'should be skipped'
        >>> # doctest: -REQUIRES(env:NOT_EXIST)
        >>> print('is-skipped')
        >>> assert False, 'should be skipped'
        >>> # doctest: -REQUIRES(--show)
        >>> print('not-skipped')
        >>> x = 'this will not be skipped'
        >>> # doctest: -REQUIRES(env:NOT_EXIST, --show, module:xdoctest)
        >>> print('not-skipped')
        >>> assert x == 'this will not be skipped'
        ''')
    self = doctest_example.DocTest(docsrc=string)
    result = self.run(on_error='raise')
    stdout = ''.join(list(self.logged_stdout.values()))
    assert result['passed']
    assert stdout.count('not-skipped') == 3
    assert stdout.count('is-skipped') == 0


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdoctest/testing/test_directive.py
        pytest ~/code/xdoctest/testing/test_directive.py
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

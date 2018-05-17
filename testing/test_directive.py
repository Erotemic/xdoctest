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


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdoctest/testing/test_directive.py
        pytest ~/code/xdoctest/testing/test_directive.py
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

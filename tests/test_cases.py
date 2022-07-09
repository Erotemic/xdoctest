from xdoctest.utils.util_misc import _run_case
from xdoctest import utils


def test_properties():
    """
    Test that all doctests are extracted from properties correctly.
    https://github.com/Erotemic/xdoctest/issues/73

    Credit: @trappitsch
    """
    text = _run_case(utils.codeblock(
        '''
        class Test(object):
            @property
            def test(self):
                """
                Example:
                    >>> ini = Test()
                    >>> ini.test
                    3.14
                """
                return 3.14

            @test.setter
            def test(self, s):
                pass
        '''))
    assert 'running 1 test' in text

    text = _run_case(utils.codeblock(
        '''
        class Test(object):
            @property
            def test(self):
                """
                Example:
                    >>> ini = Test()
                    >>> ini.test
                    3.14
                """
                return 3.14
        '''))
    assert 'running 1 test' in text

    text = _run_case(utils.codeblock(
        '''
        class Test(object):
            @property
            def test(self):
                """
                Example:
                    >>> ini = Test()
                    >>> ini.test
                    3.14
                """
                return 3.14

            @test.setter
            def test(self, s):
                """
                Example:
                    >>> ini = Test()
                    >>> ini.test = 3
                """
                pass
        '''))
    assert 'running 1 test' in text

    text = _run_case(utils.codeblock(
        '''
        class Test(object):
            @property
            def test(self):
                return 3.14

            @test.setter
            def test(self, s):
                """
                Example:
                    >>> ini = Test()
                    >>> ini.test = 3
                """
                pass
        '''))
    assert 'running 0 test' in text

    text = _run_case(utils.codeblock(
        '''
        class Test(object):
            @property
            def test(self):
                return 3.14

            @test.setter
            def test(self, s):
                """
                Example:
                    >>> ini = Test()
                    >>> ini.test = 3
                """
                pass

            @test.deleter
            def test(self, s):
                """
                Example:
                    >>> ini = Test()
                    >>> ini.test = 3
                """
                pass
        '''))
    assert 'running 0 test' in text

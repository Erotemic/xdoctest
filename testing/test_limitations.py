"""
Tests in this file are more demonstrations of the limitations of the static
analysis doctest parser.
"""
from xdoctest import utils
from xdoctest.utils.util_misc import _run_case


def test_pathological_property_case():
    """
    This case actually wont error, but it displays a limitation of static
    analysis. We trick the doctest node parser into thinking there is a setter
    property when there really isn't.
    """
    text = _run_case(utils.codeblock(
        '''
        def property(x):
            class Foo():
                def setter(self, x):
                    return x
            return Foo()

        class Test(object):
            @property
            def test(self):
                """
                Example:
                    >>> print('not really a getter')
                """
                return 3.14

            @test.setter
            def test(self, s):
                """
                Example:
                    >>> print('not really a setter')
                """
                pass
        '''))
    # If there was a way to make this case fail, that would be ok
    assert 'Test.test:0' in text
    # assert 'Test.test.fset:0' in text

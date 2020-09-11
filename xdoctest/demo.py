"""
This file contains quick demonstrations of how to use xdoctest

CommandLine:
    xdoctest -m xdoctest.demo

    xdoctest -m xdoctest.demo --verbose 0
    xdoctest -m xdoctest.demo --silent
    xdoctest -m xdoctest.demo --quiet
"""


def myfunc():
    """
    Demonstrates how to write a doctest.
    Prefix with `>>>` and ideally place in an `Example:` block.
    You can also change Example, Ignore will
    Prefix with `>>>` and ideally place in an `Example:` block.

    CommandLine:
        # it would be nice if sphinx.ext.napoleon could handle this
        xdoctest -m ~/code/xdoctest/xdoctest/demo.py myfunc

    Example:
        >>> result = myfunc()
        >>> assert result == 123

    Ignore:
        >>> # it would be nice if sphinx.ext.napoleon could ignore this
        >>> print('this test is not run')
    """
    return 123


class MyClass(object):
    """
    Example:
        >>> self = MyClass.demo()
        >>> print('self.data = {!r}'.format(self.data))
    """
    def __init__(self, *args, **kw):
        """
        Example:
            >>> # xdoctest: +REQUIRES(--fail)
            >>> raise Exception
        """
        self.data = (args, kw)

    @classmethod
    def demo(cls, **kw):
        """
        CommandLine:
            xdoctest -m ~/code/xdoctest/xdoctest/demo.py MyClass.demo
            xdoctest -m ~/code/xdoctest/xdoctest/demo.py MyClass.demo --say

        Example:
            >>> print('starting my doctest')
            >>> self = MyClass.demo(demo='thats my demo')
            >>> # xdoc: +REQUIRES(--say)
            >>> print('self.data = {!r}'.format(self.data))
        """
        return MyClass(['spam'] * 42, ['eggs'],  **kw)

    def always_fails():
        """
        CommandLine:
            xdoctest -m ~/code/xdoctest/xdoctest/demo.py MyClass.always_fails
            xdoctest -m ~/code/xdoctest/xdoctest/demo.py MyClass.always_fails --fail
            xdoctest -m ~/code/xdoctest/xdoctest/demo.py MyClass.always_fails --fail --really

            xdoctest -m ~/code/xdoctest/xdoctest/demo.py MyClass.always_fails:0 --fail
            xdoctest -m ~/code/xdoctest/xdoctest/demo.py MyClass.always_fails:1 --fail
            xdoctest -m ~/code/xdoctest/xdoctest/demo.py MyClass.always_fails:2 --fail
            xdoctest -m ~/code/xdoctest/xdoctest/demo.py MyClass.always_fails:3 --fail --really

        Example:
            >>> # xdoctest: +REQUIRES(--fail)
            >>> raise Exception('doctest always fails')

        Example:
            >>> # xdoctest: +REQUIRES(--fail)
            >>> MyClass.demo().always_fails()

        Example:
            >>> # xdoctest: +REQUIRES(--fail)
            >>> print('there is no way to fail')
            There are so many ways to fail

        Example:
            >>> # xdoctest: +REQUIRES(--fail)
            >>> # xdoctest: +REQUIRES(--really)
            >>> raise Exception  # xdoctest: +SKIP
            >>> print('did you know')  # xdoctest: +IGNORE_WANT
            directives are useful
            >>> print('match this')
            ...
            >>> print('match this')  # xdoctest: -ELLIPSIS
            ...
        """
        raise Exception('func always fails')

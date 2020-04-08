"""
https://tohtml.com/
"""
import operator


# def paragraph(text):
#     r"""
#     Remove leading, trailing, and double whitespace from multi-line strings.

#     Args:
#         text (str): typically in the form of a multiline string

#     Returns:
#         str: the reduced text block
#     """
#     import re
#     out = re.sub(r'\s\s*', ' ', text).strip()
#     return out


# def paragraph(text):
#     r"""
#     Remove leading, trailing, and double whitespace from multi-line strings.

#     Args:
#         text (str): typically in the form of a multiline string

#     Returns:
#         str: the reduced text block

#     Example:
#         >>> text = (
#         >>>     '''
#         >>>     Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
#         >>>     eiusmod tempor incididunt ut labore et dolore magna aliqua.
#         >>>     ''')
#         >>> out = paragraph(text)
#         >>> assert chr(10) in text and chr(10) not in out
#     """
#     import re
#     out = re.sub(r'\s\s*', ' ', text).strip()
#     return out


def paragraph(text):
    r"""
    Remove leading, trailing, and double whitespace from multi-line strings.

    Args:
        text (str): typically in the form of a multiline string

    Returns:
        str: the reduced text block

    Example:
        >>> text = (
                '''
                Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
                eiusmod tempor incididunt ut labore et dolore magna aliqua.
                ''')
        >>> out = paragraph(text)
        >>> assert chr(10) in text and chr(10) not in out
    """
    import re
    out = re.sub(r'\s\s*', ' ', text).strip()
    return out


# text = (
#     '''
#     Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
#     eiusmod tempor incididunt ut labore et dolore magna aliqua.
#     ''')
# out = paragraph(text)
# assert chr(10) in text and chr(10) not in out


# def paragraph(text):
#     r"""
#     Remove leading, trailing, and double whitespace from multi-line strings.

#     Args:
#         text (str): typically in the form of a multiline string

#     Returns:
#         str: the reduced text block

#     Example:
#         >>> text = (
#         ...     '''
#         ...     Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
#         ...     eiusmod tempor incididunt ut labore et dolore magna aliqua.
#         ...     ''')
#         >>> out = paragraph(text)
#         >>> assert chr(10) in text and chr(10) not in out
#     """
#     import re
#     out = re.sub(r'\s\s*', ' ', text).strip()
#     return out


# def allsame1(iterable, eq=operator.eq):
#     """
#     Determine if all items in a sequence are the same

#     Args:
#         iterable (Iterable): items to determine if they are all the same

#         eq (Callable, optional): function to determine equality
#             (default: operator.eq)

#     Example:
#         >>> allsame([1, 1, 1, 1])
#         True
#         >>> allsame([])
#         True
#         >>> allsame([0, 1])
#         False
#         >>> iterable = iter([0, 1, 1, 1])
#         >>> next(iterable)
#         >>> allsame(iterable)
#         True
#         >>> allsame(range(10))
#         False
#         >>> allsame(range(10), lambda a, b: True)
#         True
#     """
#     iter_ = iter(iterable)
#     try:
#         first = next(iter_)
#     except StopIteration:
#         return True
#     return all(eq(first, item) for item in iter_)


def allsame(iterable, eq=operator.eq):
    """
    Determine if all items in a sequence are the same

    Args:
        iterable (Iterable): items to determine if they are all the same

        eq (Callable, optional): function to determine equality
            (default: operator.eq)

    Example:
        >>> allsame([1, 1, 1, 1])
        True
        >>> allsame([])
        True
        >>> allsame([0, 1])
        False
        >>> iterable = iter([0, 1, 1, 1])
        >>> next(iterable)
        >>> allsame(iterable)
        True
        >>> allsame(range(10))
        False
        >>> allsame(range(10), lambda a, b: True)
        True
    """
    iter_ = iter(iterable)
    try:
        first = next(iter_)
    except StopIteration:
        return True
    return all(eq(first, item) for item in iter_)


def demo_directive():
    """
    Example:
        >>> print('This is run')
        >>> print('This is not run')  # xdoctest: +SKIP
        >>> # xdoctest: +SKIP
        >>> print('Skip has been enabled, commands will not run')
        >>> print('This is also not run')
        >>> print('Block based directives can be deactivated')
        >>> # xdoctest: -SKIP
        >>> print('This will now run')
    """
    pass


if __name__ == '__main__':
    """
    CommandLine:
        python -m doctest ~/code/xdoctest/dev/talk.py
        python -m xdoctest ~/code/xdoctest/dev/talk.py demo_directive
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

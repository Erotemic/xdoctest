








def foo():
    """
    Example:
        >>> # ENABLE_DOCTEST
        >>> from xdoctest.docscrape_google import *  # NOQA
        >>> docstr = split_google_docblocks.__doc__
        >>> groups = split_google_docblocks(docstr)
        >>> #print('groups = %s' % (groups,))
        >>> print(len(groups))
        >>> assert len(groups) == 3
        >>> print([g[0] for g in groups])
    """


if __name__ == '__main__':
    """
    python -m oldway foo
    pytest --xdoctest oldway.py::foo:0
    """
    import utool as ut
    ut.doctest_funcs()

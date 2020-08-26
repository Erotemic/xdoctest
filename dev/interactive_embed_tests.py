

def interative_test_xdev_embed():
    """
    CommandLine:
        xdoctest -m dev/interactive_embed_tests.py interative_test_xdev_embed

    Example:
        >>> interative_test_xdev_embed()
    """
    import xdev
    with xdev.embed_on_exception_context:
        raise Exception


def interative_test_ipdb_embed():
    """
    CommandLine:
        xdoctest -m dev/interactive_embed_tests.py interative_test_ipdb_embed

    Example:
        >>> interative_test_ipdb_embed()
    """
    import ipdb
    with ipdb.launch_ipdb_on_exception():
        raise Exception

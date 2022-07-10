"""
Global state initialized at import time.
Used for hidden arguments and developer features.
"""
import os
import sys


def _boolean_environ(key):
    """
    Args:
        key (str)

    Returns:
        bool
    """
    value = os.environ.get(key, '').lower()
    TRUTHY_ENVIRONS = {'true', 'on', 'yes', '1'}
    return value in TRUTHY_ENVIRONS


DEBUG = _boolean_environ('XDOCTEST_DEBUG') or '--debug' in sys.argv

DEBUG_PARSER = DEBUG or _boolean_environ('XDOCTEST_DEBUG_PARSER')
DEBUG_CORE = DEBUG or _boolean_environ('XDOCTEST_DEBUG_CORE')
DEBUG_RUNNER = DEBUG or _boolean_environ('XDOCTEST_DEBUG_RUNNER')
DEBUG_DOCTEST = DEBUG or _boolean_environ('XDOCTEST_DEBUG_DOCTEST')

#!/usr/bin/env python
if __name__ == '__main__':
    import pytest
    import sys
    # NOTE: it is important to return the correct error code
    sys.exit(pytest.main([
        '-p', 'pytester',
        '-p', 'no:doctest',
        '--cov=xdoctest',
        '--cov-config', '.coveragerc',
        '--cov-report', 'html',
        '--cov-report', 'term',
        '--xdoctest',
    ] + sys.argv[1:]))

#!/usr/bin/env python
if __name__ == '__main__':
    import pytest
    import sys

    try:
        import xdoctest
    except ImportError as ex:
        print("FAIL XDOCTEST IMPORT")
        print('ex = {!r}'.format(ex))
        print("FAIL XDOCTEST IMPORT")
        raise

    # NOTE: import to return the correct error code
    sys.exit(pytest.main([
        '-p', 'pytester',
        '-p', 'no:doctest',
        '--cov=xdoctest',
        '--cov-config', '.coveragerc',
        '--cov-report', 'html',
        '--cov-report', 'term',
        '--xdoctest',
    ] + sys.argv[1:]))
    # pytest.main(['-p', 'no:doctest', '-p', 'pytester', '--xdoctest', './testing'] + sys.argv[1:])
    # pytest.main(['-p', 'no:doctest', '-p', 'pytester', '--xdoctest', './xdoctest'] + sys.argv[1:])
    # pytest.main(['-p', 'no:doctest', '-p', 'pytester', '--xdoctest'] + sys.argv[1:])
    # pytest.main(['-rsxX', '-p', 'pytester', 'xdoctest'] + sys.argv[1:])
    # pytest.main(['-rsxX', '-p', 'pytester', 'xdoctest/tests'])

#     pass
# pytest -rxsX -p pytester xdoctest/tests
# #pytest -rxsX -p pytester xdoctest/tests --xdoctest-modules

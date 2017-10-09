#!/usr/bin/env python
if __name__ == '__main__':
    import pytest
    import sys
    pytest.main(['-p', 'no:doctest', '-p', 'pytester', '--xdoctest', './testing'] + sys.argv[1:])
    # pytest.main(['-p', 'no:doctest', '-p', 'pytester', '--xdoctest', './xdoctest'] + sys.argv[1:])
    # pytest.main(['-p', 'no:doctest', '-p', 'pytester', '--xdoctest'] + sys.argv[1:])
    # pytest.main(['-rsxX', '-p', 'pytester', 'xdoctest'] + sys.argv[1:])
    # pytest.main(['-rsxX', '-p', 'pytester', 'xdoctest/tests'])

#     pass
# pytest -rxsX -p pytester xdoctest/tests
# #pytest -rxsX -p pytester xdoctest/tests --xdoctest-modules

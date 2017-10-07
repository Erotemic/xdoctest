#!/usr/bin/env python
if __name__ == '__main__':
    import pytest
    # pytest.main(['-rsxX', '-p', 'pytester', 'xdoctest/tests'])
    import sys
    pytest.main(['-rsxX', '-p', 'pytester', 'xdoctest', '-xdoctest', 'testing'] + sys.argv[1:])
#     pass
# pytest -rxsX -p pytester xdoctest/tests
# #pytest -rxsX -p pytester xdoctest/tests --xdoctest-modules

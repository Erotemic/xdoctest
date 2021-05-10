#!/usr/bin/env python
# -*- coding: utf-8 -*-
if __name__ == '__main__':
    import pytest
    import sys
    package_name = 'xdoctest'
    pytest_args = [
        '-p', 'pytester',
        '-p', 'no:doctest',
        '--xdoctest',
        '--cov-config', '.coveragerc',
        '--cov-report', 'html',
        '--cov-report', 'term',
        '--cov=' + package_name,
        package_name, 'testing'
    ]
    pytest_args = pytest_args + sys.argv[1:]
    print('pytest.__version__ = {!r}'.format(pytest.__version__))
    print('pytest_args = {!r}'.format(pytest_args))
    ret = pytest.main(pytest_args)
    print('ret = {!r}'.format(ret))
    sys.exit(ret)

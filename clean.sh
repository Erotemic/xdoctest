#!/bin/bash
echo "start clean"

rm -rf _skbuild
rm -rf coverage.xml
rm -rf -- *.so
rm -rf build
rm -rf xdoctest.egg-info
rm -rf src/xdoctest.egg-info
rm -rf dist
rm -rf docs/build
rm -rf mb_work
rm -rf wheelhouse
rm -rf .pytest_cache
rm -rf pip-wheel-metadata
rm -rf htmlcov
rm -rf .coverage
rm -rf __pycache__
rm -rf tests/pybind11_test/tmp
rm -rf tests/pybind11_test/_skbuild
rm -rf tests/pybind11_test/my_ext.egg-info

rm -rf .mypy_cache

rm distutils.errors 2&> /dev/null || echo "skip rm"

CLEAN_PYTHON='find . -iname *.pyc -delete ; find . -iname *.pyo -delete ; find . -regex ".*\(__pycache__\|\.py[co]\)" -delete'
bash -c "$CLEAN_PYTHON"

echo "finish clean"

__fixperm_notes__="""

chmod o+rw .
chmod o+rw -R *
"""

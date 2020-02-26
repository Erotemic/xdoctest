#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pip install --target="$(pwd)" .
"""
from setuptools import find_packages
from skbuild import setup


if __name__ == '__main__':
    setup(
        name="my_ext",
        packages=find_packages('.'),
    )

# encoding: utf-8
from setuptools import setup


if __name__ == '__main__':
    setup(
        name="xdoctest",
        packages=['xdoctest'],
        # the following makes a plugin available to pytest
        entry_points={
            'pytest11': [
                'xdoctest = xdoctest.plugin',
            ]
        },
        # custom PyPI classifier for pytest plugins
        classifiers=[
            "Framework :: Pytest",
        ],
    )

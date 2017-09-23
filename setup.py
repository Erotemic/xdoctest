# encoding: utf-8
from setuptools import setup


if __name__ == '__main__':
    setup(
        name="doctest2",
        packages=['doctest2'],
        # the following makes a plugin available to pytest
        entry_points={
            'pytest11': [
                'doctest2 = doctest2.plugin',
            ]
        },
        # custom PyPI classifier for pytest plugins
        classifiers=[
            "Framework :: Pytest",
        ],
    )

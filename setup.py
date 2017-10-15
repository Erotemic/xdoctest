# encoding: utf-8
"""
Installation:
    pip install git+https://github.com/Erotemic/xdoctest.git

Developing:
    git clone https://github.com/Erotemic/xdoctest.git
    pip install -e xdoctest

Pypi:
     # Presetup
     pip install twine

     # First tag the source-code
     VERSION=$(python -c "import setup; print(setup.parse_version())")
     echo $VERSION
     git tag $VERSION -m "tarball tag $VERSION"
     git push --tags origin master

     # NEW API TO UPLOAD TO PYPI
     # https://packaging.python.org/tutorials/distributing-packages/

     # Build wheel or source distribution
     python setup.py bdist_wheel --universal

     # Use twine to upload. This will prompt for username and password
     twine upload --username erotemic --skip-existing dist/*

     # Check the url to make sure everything worked
     https://pypi.org/project/xdoctest/

     # ---------- OLD ----------------
     # Check the url to make sure everything worked
     https://pypi.python.org/pypi?:action=display&name=xdoctest

"""
from setuptools import setup

setupkw = dict(
    author='Jon Crall',
    name='xdoctest',
    author_email='erotemic@gmail.com',
    url='https://github.com/Erotemic/xdoctest',
    license='Apache 2',
    packages=['xdoctest'],
)


def parse_version():
    """ Statically parse the version number from __init__.py """
    from os.path import dirname, join
    import ast
    modname = setupkw['name']
    init_fpath = join(dirname(__file__), modname, '__init__.py')
    with open(init_fpath) as file_:
        sourcecode = file_.read()
    pt = ast.parse(sourcecode)
    class VersionVisitor(ast.NodeVisitor):
        def visit_Assign(self, node):
            for target in node.targets:
                if target.id == '__version__':
                    self.version = node.value.s
    visitor = VersionVisitor()
    visitor.visit(pt)
    return visitor.version


def parse_requirements(fname='requirements.txt'):
    """
    python -c "import setup; print(setup.parse_requirements())"
    """
    from os.path import dirname, join, exists
    require_fpath = join(dirname(__file__), fname)
    # This breaks on pip install, so check that it exists.
    if exists(require_fpath):
        with open(require_fpath, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
            lines = [line for line in lines if not line.startswith('#')]
            return lines


if __name__ == '__main__':
    setup(
        version=parse_version(),
        description='A rewrite of the builtin doctest module',
        install_requires=parse_requirements('requirements.txt'),
        extras_require={
            'all': parse_requirements('optional-requirements.txt')
        },
        # long_description=parse_description(),
        # the following makes a plugin available to pytest
        entry_points={
            'pytest11': [
                'xdoctest = xdoctest.plugin',
            ]
        },
        # custom PyPI classifier for pytest plugins
        classifiers=[
            'Framework :: Pytest',
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Utilities',
            # This should be interpreted as Apache License v2.0
            'License :: OSI Approved :: Apache Software License',
            # Supported Python versions
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
        ],
        **setupkw
    )

# encoding: utf-8
"""
Installation:
    pip install git+https://github.com/Erotemic/xdoctest.git

Developing:
    git clone https://github.com/Erotemic/xdoctest.git
    pip install -e xdoctest

Pypi:
    cd ~/code/xdoctest

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

Notes:
    In case you need to delete a tag
    git push --delete origin tagname
    git tag --delete tagname
"""
from setuptools import setup

setupkw = dict(
    author='Jon Crall',
    name='xdoctest',
    author_email='erotemic@gmail.com',
    url='https://github.com/Erotemic/xdoctest',
    license='Apache 2',
    packages=['xdoctest', 'xdoctest/utils', 'xdoctest/docstr'],
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
    Parse the package dependencies listed in a requirements file but strips
    specific versioning information.

    CommandLine:
        python -c "import setup; print(setup.parse_requirements())"
    """
    from os.path import dirname, join, exists
    import re
    require_fpath = join(dirname(__file__), fname)
    # This breaks on pip install, so check that it exists.
    if exists(require_fpath):
        with open(require_fpath, 'r') as f:
            packages = []
            for line in f.readlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith('-e '):
                        package = line.split('#egg=')[1]
                        packages.append(package)
                    else:
                        pat = '|'.join(['>', '>=', '=='])
                        package = re.split(pat, line)[0]
                        packages.append(package)
            return packages
    return []


def parse_description():
    """
    Parse the description in the README file

    CommandLine:
        pandoc --from=markdown --to=rst --output=README.rst README.md
        python -c "import setup; print(setup.parse_description())"
    """
    from os.path import dirname, join, exists
    readme_fpath = join(dirname(__file__), 'README.rst')
    # This breaks on pip install, so check that it exists.
    if exists(readme_fpath):
        with open(readme_fpath, 'r') as f:
            text = f.read()
        return text
    return ''


if __name__ == '__main__':
    setup(
        version=parse_version(),
        description='A rewrite of the builtin doctest module',
        install_requires=parse_requirements('requirements.txt'),
        extras_require={
            'all': parse_requirements('optional-requirements.txt')
        },
        long_description=parse_description(),
        entry_points={
            # the pytest11 entry point makes the plugin available to pytest
            'pytest11': [
                'xdoctest = xdoctest.plugin',
            ],
            # the console_scripts entry point creates the xdoctest executable
            'console_scripts': [
                'xdoctest = xdoctest.__main__:main'
            ]
        },
        # custom PyPI classifier for pytest plugins
        classifiers=[
            'Framework :: Pytest',
            'Development Status :: 4 - Beta',
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

from os.path import dirname
from os.path import join
from xdoctest import utils


__NOTES__ = """

Test this in docker

# cd ~/code/xdoctest

DOCKER_IMAGE=circleci/python:3.9-rc
docker pull $DOCKER_IMAGE
docker run -v $PWD:/io \
    --rm -it $DOCKER_IMAGE bash

docker pull python:3.9.0a5-buster
docker run -v $PWD:/io \
    --rm -it python bash


print('feature.compiler_flag = {!r:>60}'.format(bin(221184)))
for key in __future__.all_feature_names:
    feature = getattr(__future__, key, None)
    print('feature.compiler_flag = {!r:>60}'.format(key + ' ' +bin(feature.compiler_flag)))

feature.compiler_flag =                                      'nested_scopes 0b10000'
feature.compiler_flag =                                             'generators 0b0'
feature.compiler_flag =                          'with_statement 0b1000000000000000'
feature.compiler_flag =                       'barry_as_FLUFL 0b1000000000000000000'
feature.compiler_flag =                      'generator_stop 0b10000000000000000000'
feature.compiler_flag =                        'annotations 0b100000000000000000000'
feature.compiler_flag =                                       '0b110110000000000000

feature.compiler_flag =                         'print_function 0b10000000000000000'
feature.compiler_flag =                      'unicode_literals 0b100000000000000000'
feature.compiler_flag =                                  'division 0b10000000000000'
feature.compiler_flag =                          'absolute_import 0b100000000000000'

feature.compiler_flag =                     'print_function 0b100000000000000000000'

feature.compiler_flag =                                      'nested_scopes 0b10000'
feature.compiler_flag =                                             'generators 0b0'
feature.compiler_flag =                              'division 0b100000000000000000'
feature.compiler_flag =                      'absolute_import 0b1000000000000000000'
feature.compiler_flag =                      'with_statement 0b10000000000000000000'
feature.compiler_flag =                  'unicode_literals 0b1000000000000000000000'
feature.compiler_flag =                   'barry_as_FLUFL 0b10000000000000000000000'
feature.compiler_flag =                  'generator_stop 0b100000000000000000000000'
feature.compiler_flag =                    'annotations 0b1000000000000000000000000'


./python -c "import __future__; print(__future__.print_function.compiler_flag | __future__.division.compiler_flag | __future__.unicode_literals.compiler_flag | __future__.absolute_import.compiler_flag)"

__future__.



print(eval(compile('[i for i in range(3)]', mode='eval', filename='foo', flags=221184)))
print(eval(compile('[i for i in range(3)]', mode='eval', filename='foo', flags=221184)))


./python -c "eval(compile('[i for i in range(3)]', mode='single', filename='fo', flags=0, dont_inherit=True), {})"


./python -c "import __future__; print(eval(compile('[i for i in range(3)]', mode='eval', filename='fo', flags=__future__.print_function.compiler_flag | __future__.division.compiler_flag | __future__.unicode_literals.compiler_flag | __future__.absolute_import.compiler_flag)))"

./python -c "print(eval(compile('[i for i in range(3)]', mode='eval', filename='foo', flags=221184, dont_inherit=True), {}))"

python -c "print(eval('[i for i in range(3)]', {}))"
ipython -c "print(eval('[i for i in range(3)]', {}))"
ipython -c "print(eval('[i for i in range(3)]'))"
ipython -c "print(eval('[i for i in range(3)]'))"


python -c "eval('print([i for i in range(3)])', {})"


# cd /io

mkdir -p $HOME/code
cd $HOME/code
git clone -b dev/hotfix https://github.com/Erotemic/xdoctest.git
cd $HOME/code/xdoctest
pip install -e .[all]

python testing/test_binary_ext.py build_demo_extmod


cd /io/testing/pybind11_test
mkdir -p /io/testing/pybind11_test/build
cd /io/testing/pybind11_test/build
cmake ..


"""


def build_demo_extmod():
    """
    CommandLine:
        python testing/test_binary_ext.py build_demo_extmod
    """
    import os
    import glob
    import sys
    import platform

    plat_impl = platform.python_implementation()
    if plat_impl == 'PyPy':
        import pytest
        pytest.skip('pypy not supported')

    if sys.platform.startswith('win32'):
        import pytest
        pytest.skip('win32 not supported YET')

    try:
        import skbuild  # NOQA
        import pybind11  # NOQA
        import cmake  # NOQA
        import ninja  # NOQA
    except Exception:
        import pytest
        pytest.skip('skbuild, ninja, cmake, or pybind11 not available')

    testing_dpath = dirname(__file__)

    verstr, details = sys.version.split(' ', 1)
    try:
        # poor man's hash (in case python wasnt built with hashlib)
        coded = (int(details.encode('utf8').hex(), 16) % (2 ** 32))
        hashid = coded.to_bytes(4, 'big').hex()
    except Exception:
        hashid = 'python2isdead'

    src_dpath = join(testing_dpath, 'pybind11_test')
    bin_dpath = join(src_dpath, 'tmp', 'install_{}.{}'.format(verstr, hashid))
    print('src_dpath = {!r}'.format(src_dpath))
    print('bin_dpath = {!r}'.format(bin_dpath))
    utils.ensuredir(bin_dpath)
    candidates = list(glob.glob(join(bin_dpath, 'my_ext.*')))
    if len(candidates) == 0:
        pip_args = ['install', '--target={}'.format(bin_dpath), src_dpath]
        print('pip_args = {!r}'.format(pip_args))
        if 0:
            pyexe = sys.executable
            ret = os.system(pyexe + ' -m pip ' + ' '.join(pip_args))
        else:
            try:
                from pip.__main__ import _main as pip_main
            except (AttributeError, ImportError):
                from pip._internal import main as pip_main

            if callable(pip_main):
                pip_main_func = pip_main
            else:
                pip_main_func = pip_main.main
            ret = pip_main_func(pip_args)

        assert ret == 0, 'unable to build our pybind11 example'
        candidates = list(glob.glob(join(bin_dpath, 'my_ext.*')))
    assert len(candidates) == 1
    extmod_fpath = candidates[0]
    return extmod_fpath


def test_run_binary_doctests():
    """
    Tests that we can run doctests in a compiled pybind11 module

    CommandLine:
        python ~/code/xdoctest/testing/test_binary_ext.py test_run_binary_doctests

    Notes:
        xdoctest -m $HOME/code/xdoctest/testing/pybind11_test/install/my_ext.cpython-38-x86_64-linux-gnu.so list --analysis=dynamic

    """
    extmod_fpath = build_demo_extmod()
    print('extmod_fpath = {!r}'.format(extmod_fpath))
    from xdoctest import runner
    # results = runner.doctest_module(extmod_fpath, analysis='auto')
    results = runner.doctest_module(extmod_fpath, analysis='dynamic',
                                    command='list', argv=[], verbose=3)
    print('results = {!r}'.format(results))

    results = runner.doctest_module(extmod_fpath, analysis='dynamic',
                                    command='all', argv=[], verbose=3)
    print('results = {!r}'.format(results))
    assert results['n_passed'] == 1


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdoctest/testing/test_binary_ext.py
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

# -*- coding: utf-8 -*-
from os.path import join
from xdoctest import utils


def test_zero_args():
    from xdoctest import runner

    source = utils.codeblock(
        '''
        # --- HELPERS ---
        def zero_args1(a=1):
            pass


        def zero_args2(*args):
            pass


        def zero_args3(**kwargs):
            pass


        def zero_args4(a=1, b=2, *args, **kwargs):
            pass


        def non_zero_args1(a):
            pass


        def non_zero_args2(a, b):
            pass


        def non_zero_args3(a, b, *args):
            pass


        def non_zero_args4(a, b, **kwargs):
            pass


        def non_zero_args5(a, b=1, **kwargs):
            pass
        ''')

    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_zero.py')

        with open(modpath, 'w') as file:
            file.write(source)

        zero_func_names = {
            example.callname
            for example in runner._gather_zero_arg_examples(modpath)
        }
        assert zero_func_names == set(['zero_args1', 'zero_args2',
                                       'zero_args3', 'zero_args4'])


if __name__ == '__main__':
    r"""
    CommandLine:
        pytest testing/test_runner.py -s
        python testing/test_runner.py test_zero_args
    """
    import pytest
    pytest.main([__file__])
    # import xdoctest
    # xdoctest.doctest_module(__file__)

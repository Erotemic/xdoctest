

# We should be able to handle these:


def issue1():
    # ISSUE: DOES NOT SKIP CORRECTLY

    def foo1():
        """
        >>> # xdoctest: +SKIP("Undefined variables")
        >>> @custom_sharded_op_impl(torch.nn.functional.linear)
        >>> def my_custom_sharded_linear(types, args, kwargs, process_group):
        >>>     ...
        >>> input = torch.rand(10, 32)
        >>> weight = sharded_tensor.rand(32, 16)
        >>> bias = torch.rand(16)
        >>> # This will call 'my_custom_sharded_linear'
        >>> torch.nn.functional.linear(input, weight, bias)
        """

    # DOES SKIP CORRECTLY, WHY?
    def foo2():
        """
        >>> @custom_sharded_op_impl(torch.nn.functional.linear)
        >>> def my_custom_sharded_linear(types, args, kwargs, process_group):
        >>>     ...
        >>> # xdoctest: +SKIP("Undefined variables")
        >>> input = torch.rand(10, 32)
        >>> weight = sharded_tensor.rand(32, 16)
        >>> bias = torch.rand(16)
        >>> # This will call 'my_custom_sharded_linear'
        >>> torch.nn.functional.linear(input, weight, bias)
        """


def issue2():
    # Should be able to parse that setup
    def CppExtension(name, sources, *args, **kwargs):
        r'''
        Creates a :class:`setuptools.Extension` for C++.

        Convenience method that creates a :class:`setuptools.Extension` with the
        bare minimum (but often sufficient) arguments to build a C++ extension.

        All arguments are forwarded to the :class:`setuptools.Extension`
        constructor.

        Example:
            >>> from setuptools import setup
            >>> from torch.utils.cpp_extension import BuildExtension, CppExtension
            >>> setup(
                 name='extension',
                 ext_modules=[
                     CppExtension(
                         name='extension',
                         sources=['extension.cpp'],
                         extra_compile_args=['-g']),
                 ],
                 cmdclass={
                     'build_ext': BuildExtension
                 })
        '''
        include_dirs = kwargs.get('include_dirs', [])
        include_dirs += include_paths()
        kwargs['include_dirs'] = include_dirs

        library_dirs = kwargs.get('library_dirs', [])
        library_dirs += library_paths()
        kwargs['library_dirs'] = library_dirs

        libraries = kwargs.get('libraries', [])
        libraries.append('c10')
        libraries.append('torch')
        libraries.append('torch_cpu')
        libraries.append('torch_python')
        kwargs['libraries'] = libraries

        kwargs['language'] = 'c++'
        return setuptools.Extension(name, sources, *args, **kwargs)

    class LSTMCell(torch.nn.Module):
        r"""A quantizable long short-term memory (LSTM) cell.

        For the description and the argument types, please, refer to :class:`~torch.nn.LSTMCell`

        Examples::

            >>> import torch.nn.quantizable as nnqa
            >>> rnn = nnqa.LSTMCell(10, 20)
            >>> input = torch.randn(3, 10)
            >>> hx = torch.randn(3, 20)
            >>> cx = torch.randn(3, 20)
            >>> output = []
            >>> for i in range(6):
                    hx, cx = rnn(input[i], (hx, cx))
                    output.append(hx)
        """
        _FLOAT_MODULE = torch.nn.LSTMCell


def non_doctests():
    """
    ~/code/pytorch/torch/distributed/launch.py
    1. Single-Node multi-process distributed training

    ::

        >>> python -m torch.distributed.launch --nproc_per_node=NUM_GPUS_YOU_HAVE
                   YOUR_TRAINING_SCRIPT.py (--arg1 --arg2 --arg3 and all other
                   arguments of your training script)

    2. Multi-Node multi-process distributed training: (e.g. two nodes)


    Node 1: *(IP: 192.168.1.1, and has a free port: 1234)*

    ::

        >>> python -m torch.distributed.launch --nproc_per_node=NUM_GPUS_YOU_HAVE
                   --nnodes=2 --node_rank=0 --master_addr="192.168.1.1"
                   --master_port=1234 YOUR_TRAINING_SCRIPT.py (--arg1 --arg2 --arg3
                   and all other arguments of your training script)

    Node 2:

    ::

        >>> python -m torch.distributed.launch --nproc_per_node=NUM_GPUS_YOU_HAVE
                   --nnodes=2 --node_rank=1 --master_addr="192.168.1.1"
                   --master_port=1234 YOUR_TRAINING_SCRIPT.py (--arg1 --arg2 --arg3
                   and all other arguments of your training script)

    """

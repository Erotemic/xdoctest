"""
Utilities that are mainly used in self-testing
"""

from __future__ import annotations

from os.path import join
import random
from .util_path import TempDir


class TempDoctest:
    """
    Creates a temporary file containing a module-level doctest for testing

    Example:
        >>> from xdoctest import core
        >>> self = TempDoctest('>>> a = 1')
        >>> doctests = list(core.parse_doctestables(self.modpath))
        >>> assert len(doctests) == 1
    """

    def __init__(self, docstr: str, modname: str | None = None) -> None:
        if modname is None:
            # make a random temporary module name
            alphabet = list(map(chr, range(97, 97 + 26)))
            modname = ''.join([random.choice(alphabet) for _ in range(8)])
        self.modname = modname
        self.docstr = docstr
        self.temp = TempDir()
        self.dpath = self.temp.ensure()
        self.modpath = join(self.dpath, self.modname + '.py')
        with open(self.modpath, 'w') as file:
            file.write("'''\n%s'''" % self.docstr)


class TempModule:
    """
    Creates a temporary directory with a python module.

    Example:
        >>> from xdoctest import core
        >>> self = TempDoctest('>>> a = 1')
        >>> doctests = list(core.parse_doctestables(self.modpath))
        >>> assert len(doctests) == 1
    """

    def __init__(self, module_text: str, modname: str | None = None) -> None:
        if modname is None:
            # make a random temporary module name
            alphabet = list(map(chr, range(97, 97 + 26)))
            modname = ''.join([random.choice(alphabet) for _ in range(8)])
        self.modname = modname
        self.module_text = module_text
        self.temp = TempDir()
        self.dpath = self.temp.ensure()
        self.modpath = join(self.dpath, self.modname + '.py')
        with open(self.modpath, 'w') as file:
            file.write(module_text)

    def print_contents(self) -> None:
        """
        For debugging on windows
        """
        import pathlib
        import os

        print(f'--- <TempModule {self!r}> ---')
        print(f'self.modname={self.modname!r}')
        print(f'self.dpath={self.dpath!r}')
        print(f'self.modpath={self.modpath!r}')
        dpath_exists1 = os.path.exists(self.dpath)
        modpath_exists1 = os.path.exists(self.modpath)
        print(f'dpath_exists1={dpath_exists1}')
        print(f'modpath_exists1={modpath_exists1}')
        dpath = pathlib.Path(self.dpath)
        print(f'dpath={dpath}')
        dpath_exists = dpath.exists()
        print(f'dpath_exists={dpath_exists!r}')
        modpath = pathlib.Path(self.modpath)
        print(f'modpath={modpath!r}')
        modpath_exists = modpath.exists()
        print(f'modpath_exists={modpath_exists!r}')
        modpath_contents = modpath.read_text()
        print(f'modpath_contents={modpath_contents!r}')
        print(f'--- </TempModule {self!r}> ---')


def _run_case(source: str, style: str = 'auto') -> str | None:
    """
    Runs all doctests in a source block

    Args:
        source (str): source code of an entire file

    TODO: run case is over-duplicated and should be separated into a test utils directory
    """
    from xdoctest import utils
    from xdoctest import runner

    COLOR = 'yellow'

    def cprint(msg, color=COLOR):
        print(utils.color_text(str(msg), COLOR))

    cprint('\n\n\n <RUN CASE> \n  ========  \n', COLOR)

    cprint('CASE SOURCE:')
    cprint('------------')
    highlighted = utils.highlight_code(source, 'python')
    numbered = utils.add_line_numbers(highlighted)
    if isinstance(numbered, list):
        numbered_text = '\n'.join(numbered)
    else:
        numbered_text = numbered
    print(utils.indent(numbered_text))

    print('')

    import hashlib

    hasher = hashlib.sha1()
    hasher.update(source.encode('utf8'))
    hashid = hasher.hexdigest()[0:8]

    with utils.TempDir() as temp:
        dpath = temp.dpath
        assert dpath is not None
        modpath = join(dpath, 'test_linenos_' + hashid + '.py')

        with open(modpath, 'w') as file:
            file.write(source)

        with utils.CaptureStdout(suppress=False) as cap:
            runner.doctest_module(modpath, 'all', argv=[''], style=style)

    cprint('\n\n --- </END RUN CASE> --- \n\n', COLOR)
    return cap.text

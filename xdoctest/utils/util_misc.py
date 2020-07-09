# -*- coding: utf-8 -*-
"""
Utilities that are mainly used in self-testing
"""
from __future__ import print_function, division, absolute_import, unicode_literals
from os.path import join
import random
from .util_path import TempDir


class TempDoctest(object):
    """
    Creates a temporary file containing a module-level doctest for testing

    Example:
        >>> from xdoctest import core
        >>> self = TempDoctest('>>> a = 1')
        >>> doctests = list(core.parse_doctestables(self.modpath))
        >>> assert len(doctests) == 1
    """
    def __init__(self, docstr, modname=None):
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


def _run_case(source, style='auto'):
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
    cprint('\n\n'
           '\n <RUN CASE> '
           '\n  ========  '
           '\n', COLOR)

    cprint('CASE SOURCE:')
    cprint('------------')
    print(utils.indent(
        utils.add_line_numbers(utils.highlight_code(source, 'python'))))

    print('')

    import hashlib
    hasher = hashlib.sha1()
    hasher.update(source.encode('utf8'))
    hashid = hasher.hexdigest()[0:8]

    with utils.TempDir() as temp:
        dpath = temp.dpath
        modpath = join(dpath, 'test_linenos_' + hashid + '.py')

        with open(modpath, 'w') as file:
            file.write(source)

        with utils.CaptureStdout(supress=False) as cap:
            runner.doctest_module(modpath, 'all', argv=[''], style=style)

    cprint('\n\n --- </END RUN CASE> --- \n\n', COLOR)
    return cap.text

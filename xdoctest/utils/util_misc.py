# -*- coding: utf-8 -*-
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
            chars = random.choices(list(map(chr, range(97, 97 + 26))), k=8)
            modname = ''.join(chars)
        self.modname = modname
        self.docstr = docstr
        self.temp = TempDir()
        self.dpath = self.temp.ensure()
        self.modpath = join(self.dpath, self.modname + '.py')
        with open(self.modpath, 'w') as file:
            file.write("'''\n%s'''" % self.docstr)

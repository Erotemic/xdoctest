# -*- coding: utf-8 -*-
"""
Checks for got-vs-want statments
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import re

unicode_literal_re = re.compile(r"(\W|^)[uU]([rR]?[\'\"])", re.UNICODE)
bytes_literal_re = re.compile(r"(\W|^)[bB]([rR]?[\'\"])", re.UNICODE)


def normalize(got, want):
    """
    Adapated from doctest_nose_plugin.py from the nltk project:
        https://github.com/nltk/nltk

    Further extended to also support byte literals.
    """
    def remove_prefixes(regex, txt):
        return re.sub(regex, r'\1\2', txt)

    # normalize whitespace
    got = got.rstrip()
    want = want.rstrip()

    got = remove_prefixes(unicode_literal_re, got)
    want = remove_prefixes(unicode_literal_re, want)

    got = remove_prefixes(bytes_literal_re, got)
    want = remove_prefixes(bytes_literal_re, want)
    return got, want


def check_output(got, want):
    if not want:
        return True
    if want:
        if want == '...':
            return True

        # Try default
        if got == want:
            return True

        got, want = normalize(got, want)
        if got == want:
            return True

    return False

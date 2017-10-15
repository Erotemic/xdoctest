# -*- coding: utf-8 -*-
"""
Checks for got-vs-want statments
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import re
from xdoctest import utils

unicode_literal_re = re.compile(r"(\W|^)[uU]([rR]?[\'\"])", re.UNICODE)
bytes_literal_re = re.compile(r"(\W|^)[bB]([rR]?[\'\"])", re.UNICODE)

BLANKLINE_MARKER = '<BLANKLINE>'
ELLIPSIS_MARKER = '...'

TRAILING_WS = re.compile(r"[ \t]*$", re.UNICODE | re.MULTILINE)


def _ellipsis_match(got, want):
    """
    The ellipsis matching algorithm taken directly from standard doctest.

    Worst-case linear-time ellipsis matching.

    CommandLine:
        python -m xdoctest.checker _ellipsis_match

    Example:
        >>> _ellipsis_match('aaa', 'aa...aa')
        False
        >>> _ellipsis_match('anything', '...')
        True
        >>> _ellipsis_match('prefix-anything', 'prefix-...')
        True
        >>> _ellipsis_match('suffix-anything', 'prefix-...')
        False
    """
    if ELLIPSIS_MARKER not in want:
        return want == got

    # Find "the real" strings.
    ws = want.split(ELLIPSIS_MARKER)
    assert len(ws) >= 2

    # Deal with exact matches possibly needed at one or both ends.
    startpos, endpos = 0, len(got)
    w = ws[0]
    if w:   # starts with exact match
        if got.startswith(w):
            startpos = len(w)
            del ws[0]
        else:
            return False
    w = ws[-1]
    if w:   # ends with exact match
        if got.endswith(w):
            endpos -= len(w)
            del ws[-1]
        else:
            return False

    if startpos > endpos:
        # Exact end matches required more characters than we have, as in
        # _ellipsis_match('aa...aa', 'aaa')
        return False

    # For the rest, we only need to find the leftmost non-overlapping
    # match for each piece.  If there's no overall match that way alone,
    # there's no overall match period.
    for w in ws:
        # w may be '' at times, if there are consecutive ellipses, or
        # due to an ellipsis at the start or end of `want`.  That's OK.
        # Search for an empty string succeeds, and doesn't change startpos.
        startpos = got.find(w, startpos, endpos)
        if startpos < 0:
            return False
        startpos += len(w)

    return True


def normalize(got, want):
    """
    Adapated from doctest_nose_plugin.py from the nltk project:
        https://github.com/nltk/nltk

    Further extended to also support byte literals.
    """
    def remove_prefixes(regex, text):
        return re.sub(regex, r'\1\2', text)

    def visible_text(lines):
        # TODO: backspaces
        # Any lines that end with only a carrage return are erased
        return [line for line in lines if not line.endswith('\r')]

    # Remove terminal colors
    got = utils.strip_ansi(got)
    want = utils.strip_ansi(want)

    # normalize python 2/3 byte/unicode prefixes
    got = remove_prefixes(unicode_literal_re, got)
    want = remove_prefixes(unicode_literal_re, want)

    got = remove_prefixes(bytes_literal_re, got)
    want = remove_prefixes(bytes_literal_re, want)

    # remove trailing whitepsace
    got = re.sub(TRAILING_WS, '', got)
    want = re.sub(TRAILING_WS, '', want)

    got_lines = got.splitlines(True)
    want_lines = want.splitlines(True)

    got_lines = visible_text(got_lines)
    want_lines = visible_text(want_lines)

    want = ''.join(want_lines)
    got = ''.join(got_lines)

    # normalize endling newlines
    want = want.rstrip()
    got = got.rstrip()

    # all whitespace normalization
    got = ' '.join(got.split())
    want = ' '.join(want.split())
    return got, want


def check_output(got, want):
    if not want:  # nocover
        return True
    if want:
        # Try default
        if got == want:
            return True

        got, want = normalize(got, want)
        if got == want:
            return True

        if _ellipsis_match(got, want):
            return True

    return False


class GotWantException(AssertionError):
    def __init__(self, msg, got, want):
        self.got = got
        self.want = want
        super(GotWantException, self).__init__(msg)

    def _do_a_fancy_diff(self, optionflags=0):
        # Not unless they asked for a fancy diff.
        got = self.got
        want = self.want
        # if not optionflags & (REPORT_UDIFF |
        #                       REPORT_CDIFF |
        #                       REPORT_NDIFF):
        #     return False

        # ndiff does intraline difference marking, so can be useful even
        # for 1-line differences.
        # if optionflags & REPORT_NDIFF:
        #     return True

        # The other diff types need at least a few lines to be helpful.
        return want.count('\n') > 2 and got.count('\n') > 2

    def output_difference(self, optionflags=0, colored=True):
        """
        Return a string describing the differences between the
        expected output for a given example (`example`) and the actual
        output (`got`).  `optionflags` is the set of option flags used
        to compare `want` and `got`.
        """
        import difflib
        got = self.got
        want = self.want
        # If <BLANKLINE>s are being used, then replace blank lines
        # with <BLANKLINE> in the actual output string.
        # if not (optionflags & DONT_ACCEPT_BLANKLINE):
        if True:
            got = re.sub('(?m)^[ ]*(?=\n)', BLANKLINE_MARKER, got)

        # TODO: colored differences
        # TODO: consolidate with checker

        # Check if we should use diff.
        if self._do_a_fancy_diff(optionflags):
            # if six.PY2:
            got = utils.ensure_unicode(got)
            # Split want & got into lines.
            want_lines = want.splitlines(True)
            got_lines = got.splitlines(True)
            # Use difflib to find their differences.
            # if optionflags & REPORT_UDIFF:
            if True:
                diff = difflib.unified_diff(want_lines, got_lines, n=2)
                diff = list(diff)[2:]  # strip the diff header
                kind = 'unified diff with -expected +actual'
            # elif optionflags & REPORT_CDIFF:
            #     diff = difflib.context_diff(want_lines, got_lines, n=2)
            #     diff = list(diff)[2:] # strip the diff header
            #     kind = 'context diff with expected followed by actual'
            # elif optionflags & REPORT_NDIFF:
            #     engine = difflib.Differ(charjunk=difflib.IS_CHARACTER_JUNK)
            #     diff = list(engine.compare(want_lines, got_lines))
            #     kind = 'ndiff with -expected +actual'
            else:
                assert 0, 'Bad diff option'
            # Remove trailing whitespace on diff output.
            diff = [line.rstrip() + '\n' for line in diff]
            diff_text = ''.join(diff)
            if colored:
                diff_text = utils.highlight_code(diff_text, lexer_name='diff')

            return 'Differences (%s):\n' % kind + utils.indent(diff_text)

        # If we're not using diff, then simply list the expected
        # output followed by the actual output.
        if want and got:
            return 'Expected:\n%s\nGot:\n%s' % (utils.indent(want), utils.indent(got))
        elif want:
            return 'Expected:\n%s\nGot nothing\n' % utils.indent(want)
        elif got:  # nocover
            assert False, 'impossible state'
            return 'Expected nothing\nGot:\n%s' % utils.indent(got)
        else:  # nocover
            assert False, 'impossible state'
            return 'Expected nothing\nGot nothing\n'


if __name__ == '__main__':
    """
    CommandLine:
        python -m xdoctest.checker
    """
    import xdoctest as xdoc
    xdoc.doctest_module()

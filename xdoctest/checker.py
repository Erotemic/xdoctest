# -*- coding: utf-8 -*-
"""
Checks for got-vs-want statments

A "got-string" is data produced by a doctest that we want to check matches som
eexpected value.

A "want-string" is a representation of the output we expect, if the
"got-string" is different than the "want-string" the doctest will fail with a
:class:`GotWantException`. A want string should come directly after a doctest
and should not be prefixed by the three cheverons (``>>> ``).

There are two types of data that a doctest could "get" as a "got-string",
either the contents of standard out the value of an expression itself.

A doctest that uses stdout might look like this

>>> print('We expect this exact string')
We expect this exact string

A doctest that uses a raw expresion might look like this

>>> def foo():
>>>     return 3
>>> foo()
3

In most cases it is best to use stdout to write your got-want tests because it
is easier to control strings sent to stdout than it is to control the
representation of expression-based "got-strings".


"""
from __future__ import print_function, division, absolute_import, unicode_literals
import re
import difflib
from xdoctest import utils
from xdoctest import constants
from xdoctest import directive

unicode_literal_re = re.compile(r"(\W|^)[uU]([rR]?[\'\"])", re.UNICODE)  # nocover
bytes_literal_re = re.compile(r"(\W|^)[bB]([rR]?[\'\"])", re.UNICODE)  # nocover

BLANKLINE_MARKER = '<BLANKLINE>'  # nocover
ELLIPSIS_MARKER = '...'  # nocover

TRAILING_WS = re.compile(r"[ \t]*$", re.UNICODE | re.MULTILINE)  # nocover


_EXCEPTION_RE = re.compile(r"""
    # Grab the traceback header.  Different versions of Python have
    # said different things on the first traceback line.
    ^(?P<hdr> Traceback\ \(
        (?: most\ recent\ call\ last
        |   innermost\ last
        ) \) :
    )
    \s* $                # toss trailing whitespace on the header.
    (?P<stack> .*?)      # don't blink: absorb stuff until...
    ^ (?P<msg> \w+ .*)   #     a line *starts* with alphanum.
    """, re.VERBOSE | re.MULTILINE | re.DOTALL)


def check_got_vs_want(want, got_stdout, got_eval=constants.NOT_EVALED,
                      runstate=None):
    """
    Determines to check against either got_stdout or got_eval, and then does
    the comparison.

    If both stdout and eval "got" outputs are specified, then the "want"
    target may match either value.

    Args:
        want (str): target to match against
        got_stdout (str): output from stdout
        got_eval (str): output from an eval statement.

    Raises:
        GotWantException - If the "got" differs from this parts want.
    """
    # If we did not want anything than ignore eval and stdout
    if got_eval is constants.NOT_EVALED:
        # if there was no eval, check stdout
        got = got_stdout
        flag = check_output(got, want, runstate)
    else:
        if not got_stdout:
            # If there was no stdout then use eval value.
            try:
                got = repr(got_eval)
            except Exception as ex:
                raise ExtractGotReprException('Error calling repr for {}. Caused by: {!r}'.format(type(got_eval), ex), ex)
            flag = check_output(got, want, runstate)
        else:
            # If there was eval and stdout, defer to stdout
            # but allow fallback on the eval.
            got = got_stdout
            flag = check_output(got, want, runstate)
            if not flag:
                # allow eval to fallback and save us, but if it fails, do a
                # diff with stdout
                got = repr(got_eval)
                flag = check_output(got, want, runstate)
                if not flag:
                    got = got_stdout
    if not flag:
        msg = 'got differs with doctest want'
        ex = GotWantException(msg, got, want)
        raise ex
    return flag


def _strip_exception_details(msg):
    # Support for IGNORE_EXCEPTION_DETAIL.
    # Get rid of everything except the exception name; in particular, drop
    # the possibly dotted module path (if any) and the exception message (if
    # any).  We assume that a colon is never part of a dotted name, or of an
    # exception name.
    # E.g., given
    #    "foo.bar.MyError: la di da"
    # return "MyError"
    # Or for "abc.def" or "abc.def:\n" return "def".

    start, end = 0, len(msg)
    # The exception name must appear on the first line.
    i = msg.find("\n")
    if i >= 0:
        end = i
    # retain up to the first colon (if any)
    i = msg.find(':', 0, end)
    if i >= 0:
        end = i
    # retain just the exception name
    i = msg.rfind('.', 0, end)
    if i >= 0:
        start = i + 1
    return msg[start: end]


def extract_exc_want(want):
    want_ = utils.codeblock(want)
    m = _EXCEPTION_RE.search(want_)
    exc_want = m.group('msg') if m else None
    return exc_want


def check_exception(exc_got, want, runstate=None):
    """
    Checks want against an exception

    Raises:
        GotWantException - If the "got" differs from this parts want.
    """
    exc_want = extract_exc_want(want)
    if exc_want is None:
        # Reraise the error if the want message is formatted like an exception
        raise
    flag = check_output(exc_got, exc_want, runstate)
    # print('exc_want = {!r}'.format(exc_want))
    # print('exc_got = {!r}'.format(exc_got))
    # print('flag = {!r}'.format(flag))

    if not flag and runstate['IGNORE_EXCEPTION_DETAIL']:
        exc_got1 = _strip_exception_details(exc_got)
        exc_want1 = _strip_exception_details(exc_want)
        flag = check_output(exc_got1, exc_want1, runstate)
        if flag:
            exc_got = exc_got1
            exc_want = exc_want1

    if not flag:
        msg = 'exception message is different'
        ex = GotWantException(msg, exc_got, exc_want)
        raise ex
    return flag


def check_output(got, want, runstate=None):
    """
    Does the actual comparison between `got` and `want`
    """
    if not want:  # nocover
        return True
    if want:
        # Try default
        if got == want:
            return True

        if runstate is None:
            runstate = directive.RuntimeState()

        got, want = normalize(got, want, runstate)
        return _check_match(got, want, runstate)
    return False


def _check_match(got, want, runstate):
    if got == want:
        return True

    if runstate['ELLIPSIS']:
        if _ellipsis_match(got, want):
            return True

    return False


def _ellipsis_match(got, want):
    r"""
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
        >>> _ellipsis_match('foo', '... foo')
        True
        >>> _ellipsis_match('took=3.4s', 'took=...s')
        True
        >>> _ellipsis_match('best=3.4s ave=4.5s', 'best=...s ave=...s')
        True
        >>> _ellipsis_match('took: 1.16e-05 s\nbest=9.63e-07 s ave=1.002e-06 ± 3e-08 s\n',
        >>>                 'took: ...s\nbest=...s ave=...s\n')
        True
    """
    if ELLIPSIS_MARKER not in want:
        return want == got

    # Find "the real" strings.
    # ws = want.split(ELLIPSIS_MARKER)
    # MODIFICATION: the ellipsis consumes all whitespace around it
    # for compatibility with whitespace normalization.
    ws = re.split(r'\s*{}\s*'.format(re.escape(ELLIPSIS_MARKER)), want,
                  flags=re.MULTILINE)
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


def normalize(got, want, runstate=None):
    r"""
    Adapated from doctest_nose_plugin.py from the nltk project:
        https://github.com/nltk/nltk

    Further extended to also support byte literals.

    Example:
        >>> want = "...\n(0, 2, {'weight': 1})\n(0, 3, {'weight': 2})"
        >>> got = "(0, 2, {'weight': 1})\n(0, 3, {'weight': 2})"
    """
    if runstate is None:
        runstate = directive.RuntimeState()

    def remove_prefixes(regex, text):
        return re.sub(regex, r'\1\2', text)

    def visible_text(lines):
        # TODO: backspaces
        # Any lines that end with only a carrage return are erased
        return [line for line in lines if not line.endswith('\r')]

    # Remove terminal colors
    if True:
        got = utils.strip_ansi(got)
        want = utils.strip_ansi(want)

    if True:
        # normalize python 2/3 byte/unicode prefixes
        got = remove_prefixes(unicode_literal_re, got)
        want = remove_prefixes(unicode_literal_re, want)

        # Note: normalizing away prefixes can cause weird "got"
        # results to print when there is a got-want mismatch.
        # For instance, if you get {'b': 22} but you want {'b': 2}
        # this will cause xdoctest to report that you wanted {'': 2}
        # because it reports the normalized version of the want message
        got = remove_prefixes(bytes_literal_re, got)
        want = remove_prefixes(bytes_literal_re, want)

    # Replace <BLANKLINE>s if it is being used.
    if not runstate['DONT_ACCEPT_BLANKLINE']:
        want = remove_blankline_marker(want)

    # always remove trailing whitepsace
    got = re.sub(TRAILING_WS, '', got)
    want = re.sub(TRAILING_WS, '', want)
    # normalize endling newlines
    want = want.rstrip()
    got = got.rstrip()

    # Always remove invisible text
    got_lines = got.splitlines(True)
    want_lines = want.splitlines(True)
    got_lines = visible_text(got_lines)
    want_lines = visible_text(want_lines)
    want = ''.join(want_lines)
    got = ''.join(got_lines)

    if runstate['NORMALIZE_WHITESPACE'] or runstate['IGNORE_WHITESPACE']:

        # all whitespace normalization
        # treat newlines and all whitespace as a single space
        got = ' '.join(got.split())
        want = ' '.join(want.split())

    if runstate['IGNORE_WHITESPACE']:
        # Completely remove whitespace
        got = re.sub(r'\s', '', got, flags=re.MULTILINE)
        want = re.sub(r'\s', '', want, flags=re.MULTILINE)

    if runstate['NORMALIZE_REPR']:
        def norm_repr(a, b):
            # If removing quotes would allow for a match, remove them.
            if not _check_match(a, b, runstate):
                for q in ['"', "'"]:
                    if a.startswith(q) and a.endswith(q):
                        if _check_match(a[1:-1], b, runstate):
                            return a[1:-1]
            return a
        got = norm_repr(got, want)
        want = norm_repr(want, got)

    return got, want


class ExtractGotReprException(AssertionError):
    """
    Exception used when we are unable to extract a string "got"
    """
    def __init__(self, msg, orig_ex):
        super(ExtractGotReprException, self).__init__(msg)
        self.orig_ex = orig_ex


class GotWantException(AssertionError):
    """
    Exception used when the "got" output of a doctest differs from the expected
    "want" output.

    """
    def __init__(self, msg, got, want):
        super(GotWantException, self).__init__(msg)
        self.got = got
        self.want = want

    def _do_a_fancy_diff(self, runstate=None):
        # Not unless they asked for a fancy diff.
        got = self.got
        want = self.want

        if runstate is None:
            runstate = directive.RuntimeState()

        # ndiff does intraline difference marking, so can be useful even
        # for 1-line differences.
        if runstate['REPORT_NDIFF']:
            return True

        # The other diff types need at least a few lines to be helpful.
        if runstate['REPORT_UDIFF'] or runstate['REPORT_CDIFF']:
            return want.count('\n') > 2 and got.count('\n') > 2

        return False

    def output_difference(self, runstate=None, colored=True):
        """
        Return a string describing the differences between the expected output
        for a given example (`example`) and the actual output (`got`).
        The `runstate` contains option flags used to compare `want` and `got`.

        Notes:
            This does not check if got matches want, it only outputs the raw
            differences. Got/Want normalization may make the differences appear
            more exagerated than they are.
        """
        got = self.got
        want = self.want

        if runstate is None:
            runstate = directive.RuntimeState()

        # Don't normalize because it usually removes the newlines
        runstate_ = runstate.to_dict()

        # Don't normalize whitespaces in report for better visibility
        runstate_['NORMALIZE_WHITESPACE'] = False
        runstate_['IGNORE_WHITESPACE'] = False
        got, want = normalize(got, want, runstate_)

        # If <BLANKLINE>s are being used, then replace blank lines
        # with <BLANKLINE> in the actual output string.
        # if not runstate['DONT_ACCEPT_BLANKLINE']:
        #     got = re.sub('(?m)^[ ]*(?=\n)', BLANKLINE_MARKER, got)

        got = utils.ensure_unicode(got)

        # Check if we should use diff.
        if self._do_a_fancy_diff(runstate):
            # Split want & got into lines.
            want_lines = want.splitlines(True)
            got_lines = got.splitlines(True)
            # Use difflib to find their differences.
            if runstate['REPORT_UDIFF']:
                diff = difflib.unified_diff(want_lines, got_lines, n=2)
                diff = list(diff)[2:]  # strip the diff header
                kind = 'unified diff with -expected +actual'
            elif runstate['REPORT_CDIFF']:
                diff = difflib.context_diff(want_lines, got_lines, n=2)
                diff = list(diff)[2:]  # strip the diff header
                kind = 'context diff with expected followed by actual'
            elif runstate['REPORT_NDIFF']:
                # TODO: Is there a way to make Differ ignore whitespace if that
                # runtime directive is specified?
                engine = difflib.Differ(charjunk=difflib.IS_CHARACTER_JUNK)
                diff = list(engine.compare(want_lines, got_lines))
                kind = 'ndiff with -expected +actual'
            else:
                raise ValueError('Invalid difflib option')

            # Remove trailing whitespace on diff output.
            diff = [line.rstrip() + '\n' for line in diff]
            diff_text = ''.join(diff)
            if colored:
                diff_text = utils.highlight_code(diff_text, lexer_name='diff')

            text = 'Differences (%s):\n' % kind + utils.indent(diff_text)
        else:
            # If we're not using diff, then simply list the expected
            # output followed by the actual output.
            if want and got:
                if colored:
                    got = utils.color_text(got, 'red')
                    want = utils.color_text(want, 'red')
                text = 'Expected:\n{}\nGot:\n{}'.format(
                    utils.indent(self.want), utils.indent(self.got))
            elif want:
                if colored:
                    got = utils.color_text(got, 'red')
                    want = utils.color_text(want, 'red')
                text = 'Expected:\n{}\nGot nothing\n'.format(utils.indent(want))
            elif got:  # nocover
                raise AssertionError('impossible state')
                text = 'Expected nothing\nGot:\n{}'.format(utils.indent(got))
            else:  # nocover
                raise AssertionError('impossible state')
                text = 'Expected nothing\nGot nothing\n'
        return text

    def output_repr_difference(self, runstate=None):
        """
        Constructs a repr difference with minimal normalization.
        """
        minimal_got = self.got.rstrip()
        minimal_want = self.want.rstrip()

        if runstate is None:
            runstate = directive.RuntimeState()

        # Don't normalize because it usually removes the newlines
        runstate_ = runstate.to_dict()

        if not runstate_['DONT_ACCEPT_BLANKLINE']:
            minimal_want = remove_blankline_marker(minimal_want)

        lines = [
            ('Repr Difference:'),
            # TODO: get a semi-normalized output before showing repr?
            ('    got  = {!r}'.format(minimal_got)),
            ('    want = {!r}'.format(minimal_want)),
        ]
        return '\n'.join(lines)


def remove_blankline_marker(text):
    r"""
    Example:
        >>> text1 = 'foo\n{}\nbar'.format(BLANKLINE_MARKER)
        >>> text2 = '{}\nbar'.format(BLANKLINE_MARKER)
        >>> text4 = 'foo\n{}'.format(BLANKLINE_MARKER)
        >>> text3 = '{}'.format(BLANKLINE_MARKER)
        >>> text5 = text1 + text1 + text1
        >>> assert BLANKLINE_MARKER not in remove_blankline_marker(text1)
        >>> assert BLANKLINE_MARKER not in remove_blankline_marker(text2)
        >>> assert BLANKLINE_MARKER not in remove_blankline_marker(text3)
        >>> assert BLANKLINE_MARKER not in remove_blankline_marker(text4)
        >>> assert BLANKLINE_MARKER not in remove_blankline_marker(text5)
    """
    pos_lb = '(?<=\n)'  # positive lookbehind
    blankline_pattern = '|'.join([
        '{pos_lb}{marker}\n', '{marker}\n',
        '\n{marker}', '{marker}']).format(
            marker=BLANKLINE_MARKER, pos_lb=pos_lb)
    # blankline_pattern = r'(?<=\n)[ ]*{}\n?'.format(re.escape(BLANKLINE_MARKER))
    new_text = re.sub(blankline_pattern, '\n', text, re.MULTILINE)
    return new_text


if __name__ == '__main__':
    """
    CommandLine:
        python -m xdoctest.checker all
    """
    import xdoctest as xdoc
    xdoc.doctest_module()

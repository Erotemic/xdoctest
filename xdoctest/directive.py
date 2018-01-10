"""
There are two types of directives: block and inline

Block directives are specified on their own line and influence the behavior
of multiple lines of code.

Inline directives are specified after in the same line of code and only
influence that line / repl part.

Example:
    >>> any(extract(' # xdoctest: skip'))
    True
    >>> any(extract(' # badprefix: not-a-directive'))
    False
    >>> any(extract(' # xdoctest: skip'))
    True
    >>> any(extract(' # badprefix: not-a-directive'))
    False
"""
import re
import warnings
from xdoctest import static_analysis as static
from xdoctest import utils


def named(key, pattern):
    """ helper for regex """
    return '(?P<{}>{})'.format(key, pattern)


class Directive(utils.NiceRepr):
    def __init__(self, name, positive=True, args=[], inline=None):
        self.name = name
        self.args = args
        self.inline = inline
        self.positive = positive

    def __nice__(self):
        prefix = ['-', '+'][int(self.positive)]
        if self.args:
            argstr = ', '.join(self.args)
            return '{}{}({})'.format(prefix, self.name, argstr)
        else:
            return '{}{}'.format(prefix, self.name)


COMMANDS = [
    'SKIP',
    'REQUIRES',

    # Currently we are only **really** trying to support skip
    'ELLIPSES',
    'NORMALIZE_WHITESPACE',
    'REPORT_UDIFF'
    'REPORT_NDIFF'
    'REPORT_CDIFF'
]
DIRECTIVE_PATTERNS = [
    #r'\s*\+\s*' + named('style1', '.*'),
    r'x?doctest:\s*' + named('style2', '.*'),
    r'x?doc:\s*' + named('style3', '.*'),
]
DIRECTIVE_RE = re.compile('|'.join(DIRECTIVE_PATTERNS), flags=re.IGNORECASE)


def extract(text):
    """
    Parses directives from a line or repl line

    Args:
        text (str): should correspond to exactly one PS1 line and its PS2
        followups.

    Notes:
        The original `doctest` module sometimes yeilded false positives for a
        directive pattern. Because `xdoctest` is parsing the text, this issue
        does not occur.

    CommandLine:
        python -m xdoctest.directive extract

    Example:
        >>> text = '# xdoctest: + SKIP'
        >>> print(', '.join(list(map(str, extract(text)))))
        <Directive(+SKIP)>

        >>> # Directive with args
        >>> text = '# xdoctest: requires(--show)'
        >>> print(', '.join(list(map(str, extract(text)))))
        <Directive(+REQUIRES(--show))>

        >>> # Malformatted directives are ignored
        >>> text = '# xdoctest: does_not_exist, skip'
        >>> print(', '.join(list(map(str, extract(text)))))
        <Directive(+SKIP)>

        >>> # Two directives in one line
        >>> text = '# xdoctest: +ELLIPSES, -NORMALIZE_WHITESPACE'
        >>> print(', '.join(list(map(str, extract(text)))))
        <Directive(+ELLIPSES)>, <Directive(-NORMALIZE_WHITESPACE)>

    """
    # The extracted directives are inline if the text only contains comments
    inline = not all(line.strip().startswith('#')
                     for line in text.splitlines())
    #
    for comment in static.extract_comments(text):
        # remove the first comment character and see if the comment matches the
        # directive pattern
        m = DIRECTIVE_RE.match(comment[1:].strip())
        if m:
            for key, optstr in m.groupdict().items():
                if optstr:
                    for directive in parse_directive_optstr(optstr, inline):
                        yield directive


def parse_directive_optstr(optstr, inline=None):
    """
    Parses the information in the directive

    optstrs are:
        optionally prefixed with `+` (default) or `-`
        comma separated
        may contain one paren enclosed argument (experimental)
        all spaces are ignored
    """
    for optpart in optstr.split(','):
        optpart = optpart.strip()
        # all spaces are ignored
        optpart = optpart.replace(' ', '')

        paren_pos = optpart.find('(')
        if paren_pos > -1:
            # handle simple paren case. TODO expand or remove
            args = [optpart[paren_pos + 1:optpart.find(')')]]
            optpart = optpart[:paren_pos]
        else:
            args = []

        # Determine if the option starts with + or - (we assume + by default)
        if optpart.startswith(('+', '-')):
            positive = not optpart.startswith('-')
            name = optpart[1:]
        else:
            positive = True
            name = optpart

        name = name.upper()
        if name not in COMMANDS:
            msg = 'Unknown directive: {!r}'.format(optpart)
            warnings.warn(msg)
        else:
            directive = Directive(name, positive, args, inline)
            yield directive


if __name__ == '__main__':
    r"""
    CommandLine:
        python -m xdoctest.directive
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

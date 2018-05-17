"""
There are two types of directives: block and inline

Block directives are specified on their own line and influence the behavior
of multiple lines of code.

Inline directives are specified after in the same line of code and only
influence that line / repl part.

Basic Directives
----------------

Basic directives correspond directly to an xdoctest runtime state attribute.
These can be modified by directly using the xdoctest directive syntax.
The following documents all supported basic directives.


Advanced Directives
-------------------

Advanced directives may take arguments and are more conditional in nature. The
names of the advanced directives do not correspond to a runtime state
attribute. Instead they represent a conditional modification of a basic runtime
state attribute.  For example, the advanced directive `+REQUIRES(flag)` will
correspond to a `+SKIP` directive if the condition (a command line argument or
platform name) represented by `flag` is satisfied.


CommandLine:
    python -m xdoctest.directive __doc__


Example:
    The following example shows how the `+SKIP` directives may be used to
    bypass certain places in the code.

    >>> # An inline directive appears on the same line as a command and
    >>> # only applies to the current line.
    >>> raise AssertionError('this will not be run (a)')  # xdoctest: +SKIP
    >>> print('This line will print: (A)')
    >>> print('This line will print: (B)')
    >>> # However, if a directive appears on its own line, then it applies
    >>> # too all subsequent lines.
    >>> # xdoctest: +SKIP
    >>> raise AssertionError('this will not be run (b)')
    >>> print('This line will not print: (A)')
    >>> # Note, that SKIP is simply a state and can be disabled to allow
    >>> # the program to continue executing.
    >>> # xdoctest: -SKIP
    >>> print('This line will print: (C)')
    >>> print('This line will print: (D)')
    >>> # This applies to inline directives as well
    >>> # xdoctest: +SKIP
    >>> raise AssertionError('this will not be run (c)')
    >>> print('This line will print: (E)')  # xdoctest: -SKIP
    >>> raise AssertionError('this will not be run (d)')
    >>> # xdoctest: -SKIP
    >>> print('This line will print: (F)')

Example:
    This next examples illustrates how to use the advanced `+REQURIES()`
    directive. Note, REQUIRES currently only modifies SKIP, but in the
    future it may track its own state.

    >>> import sys
    >>> count = 0
    >>> # xdoctest: +REQUIRES(WIN32)
    >>> assert sys.platform.startswith('win32')
    >>> count += 1
    >>> # xdoctest: +REQUIRES(LINUX)
    >>> assert sys.platform.startswith('linux')
    >>> count += 1
    >>> # xdoctest: +REQUIRES(DARWIN)
    >>> assert sys.platform.startswith('darwin')
    >>> count += 1
    >>> # xdoctest: -SKIP
    >>> print(count)
    >>> assert count == 1, 'Exactly one of the above parts should have run'
    >>> # xdoctest: +REQUIRES(--verbose)
    >>> print('This is only printed if you run with --verbose')
"""
import sys
import os
import re
import warnings
from xdoctest import static_analysis as static
from xdoctest import utils
from collections import OrderedDict
# from xdoctest import exceptions


def named(key, pattern):
    """ helper for regex """
    return '(?P<{}>{})'.format(key, pattern)


# TODO: modify global directive defaults

DEFAULT_RUNTIME_STATE = {
    'DONT_ACCEPT_BLANKLINE': False,
    'ELLIPSIS': True,
    'IGNORE_WHITESPACE': False,
    'IGNORE_EXCEPTION_DETAIL': False,
    'NORMALIZE_WHITESPACE': True,

    'IGNORE_WANT': False,

    'NORMALIZE_REPR': True,

    'REPORT_CDIFF': False,
    'REPORT_NDIFF': False,
    'REPORT_UDIFF': True,

    'SKIP': False,

    # Original directives we are currently not supporting:
    # DONT_ACCEPT_TRUE_FOR_1
    # REPORT_ONLY_FIRST_FAILURE
}


class RuntimeState(utils.NiceRepr):
    """
    Maintains the runtime state for a single `run()` of an example

    Inline directives are pushed and popped after the line is run.
    Otherwise directives persist until another directive disables it.

    Example:
        >>> from xdoctest.directive import *
        >>> runstate = RuntimeState()
        >>> assert not runstate['IGNORE_WHITESPACE']
        >>> # Directives modify the runtime state
        >>> directives = list(extract('# xdoc: -ELLIPSIS, +IGNORE_WHITESPACE'))
        >>> runstate.update(directives)
        >>> assert not runstate['ELLIPSIS']
        >>> assert runstate['IGNORE_WHITESPACE']
        >>> # Inline directives only persist until the next update
        >>> directives = [Directive('IGNORE_WHITESPACE', False, inline=True)]
        >>> runstate.update(directives)
        >>> assert not runstate['IGNORE_WHITESPACE']
        >>> runstate.update({})
        >>> assert runstate['IGNORE_WHITESPACE']

    Example:
        >>> # xdoc: +IGNORE_WHITESPACE
        >>> print(str(RuntimeState()))
        <RuntimeState({
            DONT_ACCEPT_BLANKLINE: False,
            ELLIPSIS: True,
            IGNORE_EXCEPTION_DETAIL: False,
            IGNORE_WANT: False,
            IGNORE_WHITESPACE: False,
            NORMALIZE_REPR: True,
            NORMALIZE_WHITESPACE: True,
            REPORT_CDIFF: False,
            REPORT_NDIFF: False,
            REPORT_UDIFF: True,
            SKIP: False
        })>
    """
    def __init__(self, default_state=None):
        self._global_state = DEFAULT_RUNTIME_STATE.copy()
        if default_state:
            self._global_state.update(default_state)
        self._inline_state = {}

    def to_dict(self):
        state = self._global_state.copy()
        state.update(self._inline_state)
        state = OrderedDict(sorted(state.items()))
        return state

    def __nice__(self):
        return '{' + ', '.join(['{}: {}'.format(*item)
                               for item in self.to_dict().items()]) + '}'

    def __getitem__(self, key):
        if key not in self._global_state:
            raise KeyError('Unknown key: {}'.format(key))
        if key in self._inline_state:
            return self._inline_state[key]
        else:
            return self._global_state[key]

    def __setitem__(self, key, value):
        if key not in self._global_state:
            raise KeyError('Unknown key: {}'.format(key))
        self._global_state[key] = value

    def set_report_style(self, reportchoice, state=None):
        """
        Example:
            >>> from xdoctest.directive import *
            >>> runstate = RuntimeState()
            >>> assert runstate['REPORT_UDIFF']
            >>> runstate.set_report_style('ndiff')
            >>> assert not runstate['REPORT_UDIFF']
            >>> assert runstate['REPORT_NDIFF']
        """
        # When enabling a report flag, toggle all others off
        if state is None:
            state = self._global_state
        for k in state.keys():
            if k.startswith('REPORT_'):
                state[k] = False
        state['REPORT_' + reportchoice.upper()] = True

    def update(self, directives):
        self._inline_state.clear()
        for directive in directives:
            key, value = directive.state_item()
            if key == 'NOOP':
                continue
            if key not in self._global_state:
                warnings.warn('Unknown state: {}'.format(key))
            if directive.inline:
                state = self._inline_state
            else:
                state = self._global_state

            if key.startswith('REPORT_') and value:
                self.set_report_style(key.replace('REPORT_', ''))
            state[key] = value


class Directive(utils.NiceRepr):
    """
    Directives modify the runtime state.
    """
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

    def unpack_args(self, num):
        nargs = self.args
        if len(nargs) != 1:
            raise TypeError(
                '{} directive expected exactly {} argument(s), '
                'got {}'.format(self.name, num, nargs))
        return self.args

    def state_item(self, argv=None):
        """
        Example:
            >>> Directive('SKIP').state_item()
            ('SKIP', True)
            >>> Directive('SKIP', inline=True).state_item()
            ('SKIP', True)
            >>> Directive('REQUIRES', args=['-s']).state_item(argv=['-s'])
            ('SKIP', False)
            >>> Directive('REQUIRES', args=['-s']).state_item(argv=[])
            ('SKIP', True)
            >>> Directive('ELLIPSIS', args=['-s']).state_item(argv=[])
            ('ELLIPSIS', True)
        """
        if self.name == 'REQUIRES':
            # TODO: We should probably change requires so it keeps track
            # of what you require, so we could add and remove requirements e.g.
            # +REQUIRES(WIN32)
            # we now require windows
            # +REQUIRES(--flag)
            # we now require windows AND a flag
            # -REQUIRES(WIN32)
            # we no longer require windows, but we still require the argflag

            # TODO: register these advanced directives dynamically
            # requires conditionally behaves like skip
            if argv is None:
                argv = sys.argv

            arg, = self.unpack_args(1)

            SYS_PLATFORM_TAGS = ['win32', 'linux', 'darwin', 'cywgin']
            OS_NAME_TAGS = ['posix', 'nt', 'java']

            if self.positive:
                key = 'SKIP'
                if arg.startswith('-'):
                    value = arg not in argv
                elif arg.lower() in SYS_PLATFORM_TAGS:
                    value = not sys.platform.startswith(arg.lower())
                elif arg.lower() in OS_NAME_TAGS:
                    value = not os.name.startswith(arg.lower())
                else:
                    ValueError(
                        'Argument to REQUIRES must be an PLATFORM tag or a '
                        'command line flag')
            else:
                key = 'NOOP'
                value = True
        else:
            key = self.name
            value = self.positive
        return key, value


COMMANDS = list(DEFAULT_RUNTIME_STATE.keys()) + [
    # Define extra commands that can resolve to a runtime state modification
    'REQUIRES',
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
        >>> text = '# xdoc: + SKIP'
        >>> print(', '.join(list(map(str, extract(text)))))
        <Directive(+SKIP)>

        >>> # Directive with args
        >>> text = '# xdoctest: requires(--show)'
        >>> print(', '.join(list(map(str, extract(text)))))
        <Directive(+REQUIRES(--show))>

        >>> # Malformatted directives are ignored
        >>> text = '# xdoctest: does_not_exist, skip'
        >>> import pytest
        >>> with pytest.warns(None) as record:
        >>>     print(', '.join(list(map(str, extract(text)))))
        <Directive(+SKIP)>

        >>> # Two directives in one line
        >>> text = '# xdoctest: +ELLIPSIS, -NORMALIZE_WHITESPACE'
        >>> print(', '.join(list(map(str, extract(text)))))
        <Directive(+ELLIPSIS)>, <Directive(-NORMALIZE_WHITESPACE)>

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
                    for optpart in optstr.split(','):
                        directive = parse_directive_optstr(optpart, inline)
                        if directive:
                            yield directive


def parse_directive_optstr(optpart, inline=None):
    """
    Parses the information in the directive

    optstrs are:
        optionally prefixed with `+` (default) or `-`
        comma separated
        may contain one paren enclosed argument (experimental)
        all spaces are ignored

    Example:
        >>> print(str(parse_directive_optstr('+IGNORE_WHITESPACE')))
        <Directive(+IGNORE_WHITESPACE)>
    """
    optpart = optpart.strip()
    # all spaces are ignored
    optpart = optpart.replace(' ', '')

    paren_pos = optpart.find('(')
    if paren_pos > -1:
        # handle simple paren case.
        # TODO expand or remove
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
        return directive


if __name__ == '__main__':
    """
    CommandLine:
        python -m xdoctest.directive all
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

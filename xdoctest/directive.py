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


TODO
----

* Directives are currently subject to change. The current documented behavior
is broken see GH #18. The fixing change will likely be backwards incompatible.

* Do we:
    (a) Maintain a directive stack to allow push and pop of SKIP directives
    (b) Only allow the positive form of +SKIP? And disallow negative -SKIP?
    (b.1) is the negative version of the directive every really that useful?
    (c) perhaps a +SKIP can only update the runtime state to be positive
        and -SKIP can only change to be negative (ie a failed +SKIP will not
        sudently set SKIP to False)


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
    >>> # xdoctest: -REQUIRES(WIN32)
    >>> # xdoctest: +REQUIRES(LINUX)
    >>> assert sys.platform.startswith('linux')
    >>> count += 1
    >>> # xdoctest: -REQUIRES(LINUX)
    >>> # xdoctest: +REQUIRES(DARWIN)
    >>> assert sys.platform.startswith('darwin')
    >>> count += 1
    >>> # xdoctest: -REQUIRES(DARWIN)
    >>> # xdoctest: -SKIP
    >>> print(count)
    >>> assert count == 1, 'Exactly one of the above parts should have run'
    >>> # xdoctest: +REQUIRES(--verbose)
    >>> print('This is only printed if you run with --verbose')

Example:
    >>> # New in 0.7.3: the requires directive can accept module names
    >>> # xdoctest: +REQUIRES(module:foobar)
"""
import sys
import os
import re
import copy
import warnings
import operator as op
from xdoctest import static_analysis as static
from xdoctest import utils
from collections import OrderedDict
from collections import namedtuple
# from xdoctest import exceptions


def named(key, pattern):
    """ helper for regex """
    return '(?P<{}>{})'.format(key, pattern)


# TODO: modify global directive defaults via a config file

DEFAULT_RUNTIME_STATE = {
    'DONT_ACCEPT_BLANKLINE': False,
    'ELLIPSIS': True,
    'IGNORE_WHITESPACE': False,
    'IGNORE_EXCEPTION_DETAIL': False,
    'NORMALIZE_WHITESPACE': True,

    'IGNORE_WANT': False,

    # 'IGNORE_MEASUREMENTS': False,
    # TODO: I want this flag to turn on normalization of numbers,
    # I.E: non-determenistic measurements do not cause doctest failure, but
    # other formatting errors will.

    'NORMALIZE_REPR': True,

    'REPORT_CDIFF': False,
    'REPORT_NDIFF': False,
    'REPORT_UDIFF': True,

    # Doctests will be skipped while this is True, note that test only run
    # if this is False and REQUIRES is empty.
    'SKIP': False,

    # Maintains a set unmet dependencies, ie the reasons we are skipping.
    # Doctests will be skipped while REQUIRES is non-empty and SKIP is False.
    'REQUIRES': set(),

    # Original directives we are currently not supporting:
    # DONT_ACCEPT_TRUE_FOR_1
    # REPORT_ONLY_FIRST_FAILURE
}


Effect = namedtuple('Effect', ('action', 'key', 'value'))


class RuntimeState(utils.NiceRepr):
    """
    Maintains the runtime state for a single `run()` of an example

    Inline directives are pushed and popped after the line is run.
    Otherwise directives persist until another directive disables it.

    CommandLine:
        xdoctest -m xdoctest.directive RuntimeState

    Example:
        >>> from xdoctest.directive import *
        >>> runstate = RuntimeState()
        >>> assert not runstate['IGNORE_WHITESPACE']
        >>> # Directives modify the runtime state
        >>> directives = list(Directive.extract('# xdoc: -ELLIPSIS, +IGNORE_WHITESPACE'))
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
            REQUIRES: set(...),
            SKIP: False
        })>
    """
    def __init__(self, default_state=None):
        self._global_state = copy.deepcopy(DEFAULT_RUNTIME_STATE)
        if default_state:
            self._global_state.update(default_state)
        self._inline_state = {}

    def to_dict(self):
        state = self._global_state.copy()
        state.update(self._inline_state)
        state = OrderedDict(sorted(state.items()))
        return state

    def __nice__(self):
        parts = ['{}: {}'.format(*item) for item in self.to_dict().items()]
        return ('{' + ', '.join(parts) + '}')

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
        """
        Update the runtime state given a set of directives

        Args:
            directives (List[Directive]): list of directives. The `effect`
                method is used to update this object.
        """
        # Clear the previous inline state
        self._inline_state.clear()
        for directive in directives:

            action, key, value = directive.effect()

            if action == 'noop':
                continue

            if key not in self._global_state:
                warnings.warn('Unknown state: {}'.format(key))

            # Determine if this impacts the local (inline) or global state.
            if directive.inline:
                state = self._inline_state
            else:
                state = self._global_state

            if action == 'set_report_style':
                # Special handling of report style
                self.set_report_style(key.replace('REPORT_', ''))
            elif action == 'assign':
                state[key] = value
            elif action == 'set.add':
                state[key].add(value)
            elif action == 'set.remove':
                state[key].remove(value)
            else:
                raise KeyError('unknown action {}'.format(action))


class Directive(utils.NiceRepr):
    """
    Directives modify the runtime state.
    """
    def __init__(self, name, positive=True, args=[], inline=None):
        self.name = name
        self.args = args
        self.inline = inline
        self.positive = positive

    @classmethod
    def extract(cls, text):
        """
        Parses directives from a line or repl line

        Args:
            text (str): must correspond to exactly one PS1 line and its PS2
                followups.

        Yeilds:
            Directive: directive: the parsed directives

        Notes:
            The original `doctest` module sometimes yeilded false positives for a
            directive pattern. Because `xdoctest` is parsing the text, this issue
            does not occur.

        Example:
            >>> from xdoctest.directive import Directive
            >>> text = '# xdoc: + SKIP'
            >>> print(', '.join(list(map(str, Directive.extract(text)))))
            <Directive(+SKIP)>

            >>> # Directive with args
            >>> text = '# xdoctest: requires(--show)'
            >>> print(', '.join(list(map(str, Directive.extract(text)))))
            <Directive(+REQUIRES(--show))>

            >>> # Malformatted directives are ignored
            >>> text = '# xdoctest: does_not_exist, skip'
            >>> import pytest
            >>> with pytest.warns(None) as record:
            >>>     print(', '.join(list(map(str, Directive.extract(text)))))
            <Directive(+SKIP)>

            >>> # Two directives in one line
            >>> text = '# xdoctest: +ELLIPSIS, -NORMALIZE_WHITESPACE'
            >>> print(', '.join(list(map(str, Directive.extract(text)))))
            <Directive(+ELLIPSIS)>, <Directive(-NORMALIZE_WHITESPACE)>

        Example:
            >>> any(Directive.extract(' # xdoctest: skip'))
            True
            >>> any(Directive.extract(' # badprefix: not-a-directive'))
            False
            >>> any(Directive.extract(' # xdoctest: skip'))
            True
            >>> any(Directive.extract(' # badprefix: not-a-directive'))
            False
        """
        # Flag extracted directives as inline iff the text is only comments
        inline = not all(line.strip().startswith('#')
                         for line in text.splitlines())
        #
        for comment in static.extract_comments(text):
            # remove the first comment character and see if the comment matches
            # the directive pattern
            m = DIRECTIVE_RE.match(comment[1:].strip())
            if m:
                for key, optstr in m.groupdict().items():
                    if optstr:
                        for optpart in optstr.split(','):
                            directive = parse_directive_optstr(optpart, inline)
                            if directive:
                                yield directive

    def __nice__(self):
        prefix = ['-', '+'][int(self.positive)]
        if self.args:
            argstr = ', '.join(self.args)
            return '{}{}({})'.format(prefix, self.name, argstr)
        else:
            return '{}{}'.format(prefix, self.name)

    def _unpack_args(self, num):
        nargs = self.args
        if len(nargs) != 1:
            raise TypeError(
                '{} directive expected exactly {} argument(s), '
                'got {}'.format(self.name, num, nargs))
        return self.args

    def effect(self, argv=None):
        """
        Returns how this directive modifies a RuntimeState object

        This is used by a RuntimeState object to update itself

        Returns:
            Effect: named tuple containing:
                action (str): code indicating how to update
                key (str): name of runtime state item to modify
                value (object): value to modify with

        CommandLine:
            xdoctest -m xdoctest.directive Directive.effect

        Example:
            >>> Directive('SKIP').effect()
            Effect(action='assign', key='SKIP', value=True)
            >>> Directive('SKIP', inline=True).effect()
            Effect(action='assign', key='SKIP', value=True)
            >>> Directive('REQUIRES', args=['-s']).effect(argv=['-s'])
            Effect(action='noop', key='REQUIRES', value=None)
            >>> Directive('REQUIRES', args=['-s']).effect(argv=[])
            Effect(action='set.add', key='REQUIRES', value='-s')
            >>> Directive('ELLIPSIS', args=['-s']).effect(argv=[])
            Effect(action='assign', key='ELLIPSIS', value=True)

        Doctest:
            >>> # requirement directive with module
            >>> directive = list(Directive.extract('# xdoctest: requires(module:xdoctest)'))[0]
            >>> print('directive = {}'.format(directive))
            >>> print('directive.effect() = {}'.format(directive.effect()))
            directive = <Directive(+REQUIRES(module:xdoctest))>
            directive.effect() = Effect(action='noop', key='REQUIRES', value=None)

            >>> directive = list(Directive.extract('# xdoctest: requires(module:notamodule)'))[0]
            >>> print('directive = {}'.format(directive))
            >>> print('directive.effect() = {}'.format(directive.effect()))
            directive = <Directive(+REQUIRES(module:notamodule))>
            directive.effect() = Effect(action='set.add', key='REQUIRES', value='module:notamodule')
        """
        key = self.name
        value = None

        if self.name == 'REQUIRES':
            # Special handling of REQUIRES
            if argv is None:
                argv = sys.argv
            arg, = self._unpack_args(1)
            if _is_requires_satisfied(arg, argv):
                # If the requirement is met, then do nothing,
                action = 'noop'
            else:
                # otherwise, add or remove the condtion from REQUIREMENTS,
                # depending on if the directive is positive or negative.
                value = arg
                if self.positive:
                    action = 'set.add'
                else:
                    action = 'set.remove'
        elif key.startswith('REPORT_'):
            # Special handling of report style
            if self.positive:
                action = 'noop'
            else:
                action = 'set_report_style'
        else:
            # The action overwrites state[key] using value
            action = 'assign'
            value = self.positive
        return Effect(action, key, value)


def _is_requires_satisfied(arg, argv):
    """
    Determines if the argument to a REQUIRES directive is satisfied

    Args:
        arg (str): condition code
        argv (List[str]): cmdline if arg is cmd code

    Returns:
        bool: flag - True if the requirement is met
    """
    SYS_PLATFORM_TAGS = ['win32', 'linux', 'darwin', 'cywgin']
    OS_NAME_TAGS = ['posix', 'nt', 'java']
    if arg.startswith('-'):
        flag = arg in argv
    elif arg.startswith('module:'):
        parts = arg.split(':')
        if len(parts) != 2:
            raise ValueError('xdoctest REQUIRES directive has too many parts')
        # set flag to False (aka SKIP) if the module does not exist
        modname = parts[1]
        flag = _module_exists(modname)
    elif arg.lower() in SYS_PLATFORM_TAGS:
        flag = sys.platform.startswith(arg.lower())
    elif arg.lower() in OS_NAME_TAGS:
        flag = os.name.startswith(arg.lower())
    else:
        msg = utils.codeblock(
            '''
            Argument to REQUIRES directive must be either
            (1) a PLATFORM or OS tag (e.g. win32, darwin, linux),
            (2) a command line flag prefixed with '--', or
            (3) a module prefixed with 'module:'.
            Got arg={!r}
            ''').replace('\n', ' ').strip().format(arg)
        raise ValueError(msg)
    return flag


_MODNAME_EXISTS_CACHE = {}


def _module_exists(modname):
    if modname not in _MODNAME_EXISTS_CACHE:
        from xdoctest import static_analysis as static
        modpath = static.modname_to_modpath(modname)
        exists_flag = modpath is not None
        _MODNAME_EXISTS_CACHE[modname] = exists_flag
    exists_flag = _MODNAME_EXISTS_CACHE[modname]
    return exists_flag


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


def parse_directive_optstr(optpart, inline=None):
    """
    Parses the information in the directive from the "optpart"

    optstrs are:
        optionally prefixed with `+` (default) or `-`
        comma separated
        may contain one paren enclosed argument (experimental)
        all spaces are ignored

    Returns:
        Directive: the parsed directive

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

"""
Directives special comments that influence the runtime behavior of doctests.
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

The basic directives and their defaults are as follows:

    * ``DONT_ACCEPT_BLANKLINE``: False,

    * ``ELLIPSIS``: True,

    * ``IGNORE_WHITESPACE``: False,

    * ``IGNORE_EXCEPTION_DETAIL``: False,

    * ``NORMALIZE_WHITESPACE``: True,

    * ``IGNORE_WANT``: False,

    * ``NORMALIZE_REPR``: True,

    * ``REPORT_CDIFF``: False,

    * ``REPORT_NDIFF``: False,

    * ``REPORT_UDIFF``: True,

    * ``SKIP``: False

Use ``-`` to disable a directive that is enabled by default, e.g.
``# xdoctest: -ELLIPSIS``, or use ``+`` to enable a directive that is disabled by
default, e.g. ``# xdoctest +SKIP``.


Advanced Directives
-------------------

Advanced directives may take arguments, be conditional, or modify the runtime
state in complex ways.  For instance, whereas most directives modify a boolean
value in the runtime state, the advanced ``REQUIRES`` directive either adds or
removes a value from a ``set`` of unmet requirements. Doctests will only run if
there are no unmet requirements.

Currently the only advanced directive is ``REQUIRES(.)``. Multiple arguments
may be specified, by separating them with commas. The currently available
arguments allow you to condition on:


    * Speical operating system / python implementation / python version tags, via: ``WIN32``, ``LINUX``, ``DARWIN``, ``POSIX``, ``NT``, ``JAVA``, ``CPYTHON``, ``IRONPYTHON``, ``JYTHON``, ``PYPY``, ``PY2``, ``PY3``. (e.g. ``# xdoctest +REQUIRES(WIN32)``)

    * Command line flags, via: ``--<someflag>``, (e.g. ``# xdoctest +REQUIRES(--verbose)``)

    * If a python module is installed, via: ``module:<modname>``, (e.g. ``# xdoctest +REQUIRES(module:numpy)``)

    * Environment variables, via: ``env:<varname>==<val>``, (e.g. ``# xdoctest +REQUIRES(env:MYENVIRON==1)``)


CommandLine:
    python -m xdoctest.directive __doc__


Example:
    The following example shows how the ``+SKIP`` directives may be used to
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
    This next examples illustrates how to use the advanced ``+REQURIES()``
    directive. Note, the REQUIRES and SKIP states are independent.

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
import operator
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
    # REPORTING_FLAGS
    # COMPARISON_FLAGS
}


Effect = namedtuple('Effect', ('action', 'key', 'value'))


class RuntimeState(utils.NiceRepr):
    """
    Maintains the runtime state for a single ``run()`` of an example

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
            directives (List[Directive]): list of directives. The ``effects``
                method is used to update this object.
        """
        # Clear the previous inline state
        self._inline_state.clear()
        for directive in directives:
            for effect in directive.effects():
                action, key, value = effect
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
                    try:
                        state[key].remove(value)
                    except KeyError:
                        pass
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
            The original ``doctest`` module sometimes yeilded false positives for a
            directive pattern. Because ``xdoctest`` is parsing the text, this issue
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
            >>> # xdoctest: +REQUIRES(module:pytest)
            >>> text = '# xdoctest: does_not_exist, skip'
            >>> import pytest
            >>> with pytest.warns(None) as record:
            >>>     print(', '.join(list(map(str, Directive.extract(text)))))
            <Directive(+SKIP)>

            >>> # Two directives in one line
            >>> text = '# xdoctest: +ELLIPSIS, -NORMALIZE_WHITESPACE'
            >>> print(', '.join(list(map(str, Directive.extract(text)))))
            <Directive(+ELLIPSIS)>, <Directive(-NORMALIZE_WHITESPACE)>

            >>> # Make sure commas inside parens are not split
            >>> text = '# xdoctest: +REQUIRES(module:foo,module:bar)'
            >>> print(', '.join(list(map(str, Directive.extract(text)))))
            <Directive(+REQUIRES(module:foo, module:bar))>

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
                        optparts = _split_opstr(optstr)
                        # optparts = optstr.split(',')
                        for optpart in optparts:
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
        warnings.warning('Deprecated and will be removed', DeprecationWarning)
        nargs = self.args
        if len(nargs) != 1:
            raise TypeError(
                '{} directive expected exactly {} argument(s), '
                'got {}'.format(self.name, num, nargs))
        return self.args

    def effect(self, argv=None, environ=None):
        warnings.warning('Deprecated use effects', DeprecationWarning)
        effects = self.effects(argv=argv, environ=environ)
        if len(effects) > 1:
            raise Exception('Old method cannot hanldle multiple effects')
        return effects[0]

    def effects(self, argv=None, environ=None):
        """
        Returns how this directive modifies a RuntimeState object

        This is called by :func:`RuntimeState.update` to update itself

        Args:
            argv (List[str], default=None):
                if specified, overwrite sys.argv
            environ (Dict[str, str], default=None):
                if specified, overwrite os.environ

        Returns:
            List[Effect]: list of named tuples containing:
                action (str): code indicating how to update
                key (str): name of runtime state item to modify
                value (object): value to modify with

        CommandLine:
            xdoctest -m xdoctest.directive Directive.effects

        Example:
            >>> Directive('SKIP').effects()[0]
            Effect(action='assign', key='SKIP', value=True)
            >>> Directive('SKIP', inline=True).effects()[0]
            Effect(action='assign', key='SKIP', value=True)
            >>> Directive('REQUIRES', args=['-s']).effects(argv=['-s'])[0]
            Effect(action='noop', key='REQUIRES', value='-s')
            >>> Directive('REQUIRES', args=['-s']).effects(argv=[])[0]
            Effect(action='set.add', key='REQUIRES', value='-s')
            >>> Directive('ELLIPSIS', args=['-s']).effects(argv=[])[0]
            Effect(action='assign', key='ELLIPSIS', value=True)

        Doctest:
            >>> # requirement directive with module
            >>> directive = list(Directive.extract('# xdoctest: requires(module:xdoctest)'))[0]
            >>> print('directive = {}'.format(directive))
            >>> print('directive.effects() = {}'.format(directive.effects()[0]))
            directive = <Directive(+REQUIRES(module:xdoctest))>
            directive.effects() = Effect(action='noop', key='REQUIRES', value='module:xdoctest')

            >>> directive = list(Directive.extract('# xdoctest: requires(module:notamodule)'))[0]
            >>> print('directive = {}'.format(directive))
            >>> print('directive.effects() = {}'.format(directive.effects()[0]))
            directive = <Directive(+REQUIRES(module:notamodule))>
            directive.effects() = Effect(action='set.add', key='REQUIRES', value='module:notamodule')

            >>> directive = list(Directive.extract('# xdoctest: requires(env:FOO==1)'))[0]
            >>> print('directive = {}'.format(directive))
            >>> print('directive.effects() = {}'.format(directive.effects(environ={})[0]))
            directive = <Directive(+REQUIRES(env:FOO==1))>
            directive.effects() = Effect(action='set.add', key='REQUIRES', value='env:FOO==1')

            >>> directive = list(Directive.extract('# xdoctest: requires(env:FOO==1)'))[0]
            >>> print('directive = {}'.format(directive))
            >>> print('directive.effects() = {}'.format(directive.effects(environ={'FOO': '1'})[0]))
            directive = <Directive(+REQUIRES(env:FOO==1))>
            directive.effects() = Effect(action='noop', key='REQUIRES', value='env:FOO==1')

            >>> # requirement directive with two args
            >>> directive = list(Directive.extract('# xdoctest: requires(--show, module:xdoctest)'))[0]
            >>> print('directive = {}'.format(directive))
            >>> for effect in directive.effects():
            >>>     print('effect = {!r}'.format(effect))
            directive = <Directive(+REQUIRES(--show, module:xdoctest))>
            effect = Effect(action='set.add', key='REQUIRES', value='--show')
            effect = Effect(action='noop', key='REQUIRES', value='module:xdoctest')
        """
        key = self.name
        value = None

        effects = []
        if self.name == 'REQUIRES':
            # Special handling of REQUIRES
            for arg in self.args:
                value = arg
                if _is_requires_satisfied(arg, argv=argv, environ=environ):
                    # If the requirement is met, then do nothing,
                    action = 'noop'
                else:
                    # otherwise, add or remove the condtion from REQUIREMENTS,
                    # depending on if the directive is positive or negative.
                    if self.positive:
                        action = 'set.add'
                    else:
                        action = 'set.remove'
                effects.append(Effect(action, key, value))
        elif key.startswith('REPORT_'):
            # Special handling of report style
            if self.positive:
                action = 'noop'
            else:
                action = 'set_report_style'
            effects.append(Effect(action, key, value))
        else:
            # The action overwrites state[key] using value
            action = 'assign'
            value = self.positive
            effects.append(Effect(action, key, value))
        return effects


def _split_opstr(optstr):
    """
    Simplified balanced paren logic to only split commas outside of parens

    Example:
        >>> optstr = '+FOO, REQUIRES(foo,bar), +ELLIPSIS'
        >>> _split_opstr(optstr)
        ['+FOO', 'REQUIRES(foo,bar)', '+ELLIPSIS']
    """
    import re
    stack = []
    split_pos = []
    for match in re.finditer(r',|\(|\)', optstr):
        token = match.group()
        if token == ',' and not stack:
            # Only split when there are no parens
            split_pos.append(match.start())
        elif token == '(':
            stack.append(token)
        elif token == ')':
            stack.pop()
    assert len(stack) == 0, 'parens not balanced'

    parts = []
    prev = 0
    for curr in split_pos:
        parts.append(optstr[prev:curr].strip())
        prev = curr + 1
    curr = None
    parts.append(optstr[prev:curr].strip())
    return parts


def _is_requires_satisfied(arg, argv=None, environ=None):
    """
    Determines if the argument to a REQUIRES directive is satisfied

    Args:
        arg (str): condition code
        argv (List[str]): cmdline if arg is cmd code usually ``sys.argv``
        environ (Dict[str, str]): environment variables usually ``os.environ``

    Returns:
        bool: flag - True if the requirement is met

    Example:
        >>> _is_requires_satisfied('PY2', argv=[])
        >>> _is_requires_satisfied('PY3', argv=[])
        >>> _is_requires_satisfied('cpython', argv=[])
        >>> _is_requires_satisfied('pypy', argv=[])
        >>> _is_requires_satisfied('nt', argv=[])
        >>> _is_requires_satisfied('linux', argv=[])

        >>> _is_requires_satisfied('env:FOO', argv=[], environ={'FOO': '1'})
        True
        >>> _is_requires_satisfied('env:FOO==1', argv=[], environ={'FOO': '1'})
        True
        >>> _is_requires_satisfied('env:FOO==T', argv=[], environ={'FOO': '1'})
        False
        >>> _is_requires_satisfied('env:BAR', argv=[], environ={'FOO': '1'})
        False
        >>> _is_requires_satisfied('env:BAR==1', argv=[], environ={'FOO': '1'})
        False
        >>> _is_requires_satisfied('env:BAR!=1', argv=[], environ={'FOO': '1'})
        True
        >>> _is_requires_satisfied('env:BAR!=1', argv=[], environ={'BAR': '0'})
        True
        >>> _is_requires_satisfied('env:BAR!=1')
        ...

        >>> # xdoctest: +REQUIRES(module:pytest)
        >>> import pytest
        >>> with pytest.raises(ValueError):
        >>>     _is_requires_satisfied('badflag:BAR==1', [])

        >>> import pytest
        >>> with pytest.raises(KeyError):
        >>>     _is_requires_satisfied('env:BAR>=1', argv=[], environ={'BAR': '0'})
    """
    # TODO: add python version options
    SYS_PLATFORM_TAGS = ['win32', 'linux', 'darwin', 'cywgin']
    OS_NAME_TAGS = ['posix', 'nt', 'java']
    PY_IMPL_TAGS = ['cpython', 'ironpython', 'jython', 'pypy']
    # TODO: tox tags: https://tox.readthedocs.io/en/latest/example/basic.html
    PY_VER_TAGS = ['py2', 'py3']

    arg_lower = arg.lower()

    if arg.startswith('-'):
        if argv is None:
            argv = sys.argv
        flag = arg in argv
    elif arg.startswith('module:'):
        parts = arg.split(':')
        if len(parts) != 2:
            raise ValueError('xdoctest module REQUIRES directive has too many parts')
        # set flag to False (aka SKIP) if the module does not exist
        modname = parts[1]
        flag = _module_exists(modname)
    elif arg.startswith('env:'):
        if environ is None:
            environ = os.environ
        parts = arg.split(':')
        if len(parts) != 2:
            raise ValueError('xdoctest env REQUIRES directive has too many parts')
        envexpr = parts[1]
        expr_parts = re.split('(==|!=|>=)', envexpr)
        if len(expr_parts) == 1:
            # Test if the environment variable is truthy
            env_key = expr_parts[0]
            flag = bool(environ.get(env_key, None))
        elif len(expr_parts) == 3:
            # Test if the environment variable is equal to an expression
            env_key, op_code, value = expr_parts
            env_val = environ.get(env_key, None)
            if op_code == '==':
                op = operator.eq
            elif op_code == '!=':
                op = operator.ne
            else:
                raise KeyError(op_code)
            flag = op(env_val, value)
        else:
            raise ValueError('Too many expr_parts={}'.format(expr_parts))
    elif arg_lower in SYS_PLATFORM_TAGS:
        flag = sys.platform.startswith(arg_lower)
    elif arg_lower in OS_NAME_TAGS:
        flag = os.name.startswith(arg_lower)
    elif arg_lower in PY_IMPL_TAGS:
        import platform
        flag = platform.python_implementation().startswith(arg_lower)
    elif arg_lower in PY_VER_TAGS:
        if sys.version_info[0] == 2:  # nocover
            flag = arg_lower == 'py2'
        elif sys.version_info[0] == 3:  # pragma: nobranch
            flag = arg_lower == 'py3'
        else:  # nocover
            flag = False
    else:
        msg = utils.codeblock(
            '''
            Argument to REQUIRES directive must be either
            (1) a PLATFORM or OS tag (e.g. win32, darwin, linux),
            (2) a command line flag prefixed with '--', or
            (3) a module prefixed with 'module:'.
            (4) an environment variable prefixed with 'env:'.
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
        optionally prefixed with ``+`` (default) or ``-``
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
        body = optpart[paren_pos + 1:optpart.find(')')]
        args = [a.strip() for a in body.split(',')]
        # args = [optpart[paren_pos + 1:optpart.find(')')]]
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

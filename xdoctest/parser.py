from six.moves import cStringIO as StringIO
import ast
import sys
import itertools as it
import tokenize
import re
from xdoctest import utils


class GotWantException(AssertionError):

    def __init__(self, msg, want, got):
        self.want = want
        self.got = got
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

    def output_difference(self, optionflags=0):
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

        # Check if we should use diff.
        if self._do_a_fancy_diff(optionflags):
            # Split want & got into lines.
            want_lines = want.splitlines(keepends=True)
            got_lines = got.splitlines(keepends=True)
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
            return 'Differences (%s):\n' % kind + utils.indent(''.join(diff))

        # If we're not using diff, then simply list the expected
        # output followed by the actual output.
        if want and got:
            return 'Expected:\n%s\nGot:\n%s' % (utils.indent(want), utils.indent(got))
        elif want:
            return 'Expected:\n%s\nGot nothing\n' % utils.indent(want)
        elif got:
            return 'Expected nothing\nGot:\n%s' % utils.indent(got)
        else:
            return 'Expected nothing\nGot nothing\n'


INDENT_RE = re.compile('^([ ]*)(?=\S)', re.MULTILINE)

BLANKLINE_MARKER = '<BLANKLINE>'
ELLIPSIS_MARKER = '...'


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


class memoize_method(object):
    """
    References:
        http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/
    """
    def __init__(self, function):
        self._function = function
        self._cacheName = '_cache__' + function.__name__
    def __get__(self, instance, cls=None):
        self._instance = instance
        return self
    def __call__(self, *args):
        cache = self._instance.__dict__.setdefault(self._cacheName, {})
        if args in cache:
            return cache[args]
        else:
            object = cache[args] = self._function(self._instance, *args)
            return object


class DoctestPart(object):
    def __init__(self, exec_lines, want_lines, line_offset, orig_lines=None):
        self.exec_lines = exec_lines
        self.want_lines = want_lines
        self.line_offset = line_offset
        self.orig_lines = orig_lines
        self.use_eval = False

    @property
    def n_lines(self):
        return self.n_exec_lines + self.n_want_lines

    @property
    def n_exec_lines(self):
        return len(self.exec_lines)

    @property
    def n_want_lines(self):
        if self.want_lines:
            return len(self.want_lines)
        else:
            return 0

    @property
    def source(self):
        return '\n'.join(self.exec_lines)

    @property
    def want(self):
        # options = self._find_options(source, name, lineno + s1)
        # example = DoctestPart(source, None, None, lineno=lineno + s1,
        #                       indent=indent, options=options)
        # the last part has a want
        # todo: If `want` contains a traceback message, then extract it.
        # m = _EXCEPTION_RE.match(want)
        # exc_msg = m.group('msg') if m else None
        if self.want_lines:
            return '\n'.join(self.want_lines)
        else:
            return None

    def __nice__(self):
        parts = []
        if self.line_offset is not None:
            parts.append('ln %s' % (self.line_offset))
        head_src = self.source.split('\n')[0][0:8]
        parts.append('src="%s..."' % (head_src,))
        if self.want is None:
            parts.append('want=None')
        else:
            head_wnt = self.want.split('\n')[0][0:8]
            parts.append('want="%s..."' % (head_wnt,))
        return ', '.join(parts)

    def __repr__(self):
        classname = self.__class__.__name__
        devnice = self.__nice__()
        return '<%s(%s) at %s>' % (classname, devnice, hex(id(self)))

    def __str__(self):
        classname = self.__class__.__name__
        devnice = self.__nice__()
        return '<%s(%s)>' % (classname, devnice)

    def check_got_vs_want(part, got_stdout, got_eval, not_evaled):
        # If we did not want anything than ignore eval and stdout
        if got_eval is not_evaled:
            # if there was no eval, check stdout
            got = got_stdout
            flag = part.check_stdout_got_vs_want(got)
        else:
            if not got_stdout:
                # If there was no stdout then use eval value.
                got = got_eval
                flag = part.check_eval_got_vs_want(got)
                got = repr(got_eval)
            else:
                # If there was eval and stdout, defer to stdout
                # but allow fallback on the eval.
                got = got_stdout
                flag = part.check_stdout_got_vs_want(got)
                if not flag:
                    # allow eval to fallback and save us
                    flag = part.check_eval_got_vs_want(got_eval)
                    if flag:
                        got = repr(got_eval)
        if not flag:
            # print('got = {!r}'.format(got))
            # print('part.want = {!r}'.format(part.want))
            # msg += output_difference(part.want, got)
            msg = 'got differs with doctest want'
            ex = GotWantException(msg, part.want, got)
            raise ex

    def check_eval_got_vs_want(self, got_eval):
        if not self.want:
            return True
        if self.want:
            if self.want == '...':
                return True
            if repr(got_eval) == self.want:
                return True
        return False

        # raise AssertionError(
        #     'got={!r} differs with doctest want={!r}'.format(repr(got), self.want))

    def check_stdout_got_vs_want(self, got):
        if not self.want:
            return True
        if self.want:
            if self.want == '...':
                return True
            got = got.rstrip()
            want = self.want.rstrip()
            # if got.endswith('\n') and not self.want.endswith('\n'):
            #     # allow got to have one extra newline
            #     got = got[:-1]
            if want == got:
                return True
        return False


class DoctestParser(object):

    def __init__(self, simulate_repl=False):
        self.simulate_repl = simulate_repl

    def parse(self, string):
        """
        Divide the given string into examples and intervening text.

        Example:
            >>> s = 'I am a dummy example with two parts'
            >>> x = 10
            >>> print(s)
            I am a dummy example with three parts
            >>> s = 'My purpose it so demonstrate how wants work here'
            >>> print('The new want applies ONLY to stdout')
            >>> print('given before the last want')
            >>> '''
                this wont hurt the test at all
                even though its multiline '''
            >>> y = 20
            The new want applies ONLY to stdout
            given before the last want
            >>> # Parts from previous examples are executed in the same context
            >>> print(x + y)
            30

            this is simply text, and doesnt apply to the previous doctest the
            <BLANKLINE> directive is still in effect.

        Example:
            >>> from xdoctest import parser
            >>> from xdoctest import docscrape_google
            >>> from xdoctest import core
            >>> self = parser.DoctestParser()
            >>> docstr = self.parse.__doc__
            >>> blocks = docscrape_google.split_google_docblocks(docstr)
            >>> doclineno = self.parse.__func__.__code__.co_firstlineno
            >>> key, (string, offset) = blocks[-2]
            >>> self._label_docsrc_lines(string)
            >>> doctest_parts = self.parse(string)
            >>> assert len(doctest_parts) == 4
        """
        string = string.expandtabs()
        # If all lines begin with the same indentation, then strip it.
        min_indent = min_indentation(string)
        if min_indent > 0:
            string = '\n'.join([l[min_indent:] for l in string.split('\n')])

        labeled_lines = self._label_docsrc_lines(string)
        grouped_lines = self._group_labeled_lines(labeled_lines)

        output = list(self._package_groups(grouped_lines))
        return output

    def _package_groups(self, grouped_lines):
        lineno = 0
        for chunk in grouped_lines:
            if isinstance(chunk, tuple):
                slines, wlines = chunk
                for example in self._package_chunk(slines, wlines, lineno):
                    yield example
                lineno += len(slines) + len(wlines)
            else:
                text_part = '\n'.join(chunk)
                yield text_part
                lineno += len(chunk)

    def _package_chunk(self, raw_source_lines, raw_want_lines, lineno=0):
        """
        if `self.simulate_repl` is True, then each statment is broken into its
        own part.  Otherwise, statements are grouped by the closest `want`
        statement.

        Example:
            >>> from xdoctest.parser import *
            >>> raw_source_lines = ['>>> "string"']
            >>> raw_want_lines = ['string']
            >>> self = DoctestParser()
            >>> part, = self._package_chunk(raw_source_lines, raw_want_lines)
            >>> part.source
            '"string"'
            >>> part.want
            'string

        """
        match = INDENT_RE.search(raw_source_lines[0])
        line_indent = 0 if match is None else (match.end() - match.start())

        source_lines = [p[line_indent:] for p in raw_source_lines]
        want_lines = [p[line_indent:] for p in raw_want_lines]

        exec_source_lines = [p[4:] for p in source_lines]

        # Find the line number of each standalone statment
        ps1_linenos, eval_final = self._locate_ps1_linenos(source_lines)

        def slice_example(s1, s2, want_lines=None):
            exec_lines = exec_source_lines[s1:s2]
            orig_lines = source_lines[s1:s2]
            example = DoctestPart(exec_lines, want_lines=want_lines,
                                  orig_lines=orig_lines,
                                  line_offset=lineno + s1)
            return example

        if self.simulate_repl:
            # Break down first parts which dont have any want
            for s1, s2 in zip(ps1_linenos, ps1_linenos[1:]):
                example = slice_example(s1, s2)
                yield example
        else:
            s1 = 0
            if want_lines and eval_final:
                # break the last line off so we can eval its value, but keep
                # previous groupings.
                s2 = ps1_linenos[-1]
                if s2 != s1:
                    example = slice_example(s1, s2)
                    yield example
                    s1 = s2
            s2 = None

        example = slice_example(s1, s2, want_lines)
        example.use_eval = bool(want_lines) and eval_final
        yield example

    def _group_labeled_lines(self, labeled_lines):
        # Now that lines have types, group them. This could have done this
        # above, but functinoality is split for readability.
        prev_source = None
        grouped_lines = []
        for state, group in it.groupby(labeled_lines, lambda t: t[0]):
            block = [t[1] for t in group]
            if state == 'text':
                if prev_source is not None:
                    # accept a source block without a want block
                    grouped_lines.append((prev_source, ''))
                    prev_source = None
                # accept the text
                grouped_lines.append(block)
            elif state == 'want':
                assert prev_source is not None, 'impossible'
                grouped_lines.append((prev_source, block))
                prev_source = None
            elif state == 'dsrc':
                # need to check if there is a want after us
                prev_source = block
        # Case where last block is source
        if prev_source:
            grouped_lines.append((prev_source, ''))
        return grouped_lines

    def _locate_ps1_linenos(self, source_lines):
        """
        Args:
            source_lines (list): lines belonging only to the doctest src
                these will be unindented, prefixed, and without any want.

        Example:
            >>> self = parser.DoctestParser()
            >>> source_lines = ['>>> def foo():', '>>>     return 0', '>>> 3']
            >>> linenos, eval_final = self._locate_ps1_linenos(source_lines)
            >>> assert linenos == [0, 2]
            >>> assert eval_final is True
        """
        # Strip indentation (and PS1 / PS2 from source)
        exec_source_lines = [p[4:] for p in source_lines]

        # Hack to make comments appear like executable statements
        exec_source_lines = ['_._  = None' if p.startswith('#') else p
                             for p in exec_source_lines]

        source_block = '\n'.join(exec_source_lines)
        pt = ast.parse(source_block)
        statement_nodes = pt.body
        ps1_linenos = [node.lineno - 1 for node in statement_nodes]
        NEED_16806_WORKAROUND = True
        if NEED_16806_WORKAROUND:
            ps1_linenos = self._workaround_16806(
                ps1_linenos, exec_source_lines)
        # Respect any line explicitly defined as PS2
        ps2_linenos = {
            x for x, p in enumerate(source_lines) if p[:4] != '>>> '
        }
        ps1_linenos = sorted(ps1_linenos.difference(ps2_linenos))

        # Is the last statement evaluatable?
        eval_final = isinstance(statement_nodes[-1], ast.Expr)
        return ps1_linenos, eval_final

    def _workaround_16806(self, ps1_linenos, exec_source_lines):
        """
        workaround for python issue 16806 (https://bugs.python.org/issue16806)

        Issue causes lineno for multiline strings to give the line they end on,
        not the line they start on.  A patch for this issue exists
        `https://github.com/python/cpython/pull/1800`

        Notes:
            Starting from the end look at consecutive pairs of indices to
            inspect the statment it corresponds to.  (the first statment goes
            from ps1_linenos[-1] to the end of the line list.
        """
        new_ps1_lines = []
        b = len(exec_source_lines)
        for a in ps1_linenos[::-1]:
            # the position of `b` is correct, but `a` may be wrong
            # is_balanced will be False iff `a` is wrong.
            while not is_balanced(exec_source_lines[a:b]):
                # shift `a` down until it becomes correct
                a -= 1
            # push the new correct value back into the list
            new_ps1_lines.append(a)
            # set the end position of the next string to be `a` ,
            # note, because this `a` is correct, the next `b` is
            # must also be correct.
            b = a
        ps1_linenos = set(new_ps1_lines)
        return ps1_linenos

    def _label_docsrc_lines(self, string):
        """
        Example:
            >>> from xdoctest.parser import *
            >>> # Having multiline strings in doctests can be nice
            >>> string = utils.codeblock(
                    '''
                    text
                    >>> items = ['also', 'nice', 'to', 'not', 'worry',
                    >>>          'about', '...', 'vs', '>>>']
                    ... print('but its still allowed')
                    but its still allowed

                    more text
                    ''')
            >>> self = DoctestParser()
            >>> print(self._label_docsrc_lines(string))
            [('text', 'text'),
             ('dsrc', ">>> items = ['also', 'nice', 'to', 'not', 'worry', 'about',"),
             ('dsrc', ">>>          'using', '...', 'instead', 'of', '>>>']"),
             ('dsrc', "... print('but its still allowed')"),
             ('want', 'but its still allowed'),
             ('want', ''),
             ('want', 'more text')]
        """

        def _complete_source(line, state_indent, line_iter):
            """
            helper
            remove lines from the iterator if they are needed to complete source
            """

            norm_line = line[state_indent:]  # Normalize line indentation
            prefix = norm_line[:4]
            suffix = norm_line[4:]
            assert prefix.strip() in {'>>>', '...'}, '{}'.format(prefix)
            yield line

            source_parts = [suffix]
            while not is_balanced(source_parts):
                try:
                    linex, next_line = next(line_iter)
                except StopIteration:
                    raise SyntaxError('ill-formed doctest')
                norm_line = next_line[state_indent:]
                prefix = norm_line[:4]
                suffix = norm_line[4:]
                if prefix.strip() not in {'>>>', '...', ''}:  # nocover
                    raise SyntaxError(
                        'Bad indentation in doctest on line {}: {!r}'.format(
                            linex, next_line))
                source_parts.append(suffix)
                yield next_line

        # parse and differenatiate between doctest source and want statements.
        labeled_lines = []
        state_indent = 0

        # line states
        TEXT = 'text'
        DSRC = 'dsrc'
        WANT = 'want'

        # Move through states, keeping track of points where states change
        #     text -> [text, dsrc]
        #     dsrc -> [dsrc, want, text]
        #     want -> [want, text, dsrc]
        prev_state = TEXT
        curr_state = None
        line_iter = enumerate(string.splitlines())
        for linex, line in line_iter:
            match = INDENT_RE.search(line)
            line_indent = 0 if match is None else (match.end() - match.start())
            norm_line = line[state_indent:]  # Normalize line indentation
            strip_line = line.strip()

            # Check prev_state transitions
            if prev_state == TEXT:
                # text transitions to source whenever a PS1 line is encountered
                # the PS1(>>>) can be at an arbitrary indentation
                if strip_line.startswith('>>> '):
                    curr_state = DSRC
                else:
                    curr_state = TEXT
            elif prev_state == WANT:
                # blank lines terminate wants
                if len(strip_line) == 0:
                    curr_state = TEXT
                # source-inconsistent indentation terminates want
                elif line.strip().startswith('>>> '):
                    curr_state = DSRC
                elif line_indent < state_indent:
                    curr_state = TEXT
                else:
                    curr_state = WANT
            elif prev_state == DSRC:
                if len(strip_line) == 0 or line_indent < state_indent:
                    curr_state = TEXT
                # allow source to continue with either PS1 or PS2
                elif norm_line.startswith(('>>> ', '... ')):
                    if strip_line == '...':
                        curr_state = WANT
                    else:
                        curr_state = DSRC
                else:
                    curr_state = WANT

            # Handle transitions
            if prev_state != curr_state:
                # Handle start of new states
                if curr_state == TEXT:
                    state_indent = 0
                if curr_state == DSRC:
                    # Start a new source
                    state_indent = line_indent
                    # renormalize line when indentation changes
                    norm_line = line[state_indent:]

            # continue current state
            if curr_state == DSRC:
                # source parts may consume more than one line
                for part in _complete_source(line, state_indent, line_iter):
                    labeled_lines.append((DSRC, part))
            elif curr_state == WANT:
                labeled_lines.append((WANT, line))
            elif curr_state == TEXT:
                labeled_lines.append((TEXT, line))
            prev_state = curr_state

        return labeled_lines


def is_balanced(lines):
    """
    Checks if the lines have balanced parens, brakets, curlies and strings

    Args:
        lines (list): list of strings

    Returns:
        bool : True if statment has balanced containers

    Doctest:
        >>> assert is_balanced(['print(foobar)'])
        >>> assert is_balanced(['foo = bar']) is True
        >>> assert is_balanced(['foo = (']) is False
        >>> assert is_balanced(['foo = (', "')(')"]) is True
        >>> assert is_balanced(
        ...     ['foo = (', "'''", ")]'''", ')']) is True
    """
    if sys.version_info.major == 3:
        block = '\n'.join(lines)
    else:
        block = '\n'.join(lines).encode('utf8')
    stream = StringIO()
    stream.write(block)
    stream.seek(0)
    try:
        for t in tokenize.generate_tokens(stream.readline):
            pass
    except tokenize.TokenError as ex:
        message = ex.args[0]
        if message.startswith('EOF in multi-line'):
            return False
        raise
    else:
        return True


def min_indentation(s):
    "Return the minimum indentation of any non-blank line in `s`"
    indents = [len(indent) for indent in INDENT_RE.findall(s)]
    if len(indents) > 0:
        return min(indents)
    else:
        return 0

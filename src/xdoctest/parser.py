"""
The XDoctest Parser
-------------------
This parses a docstring into one or more "doctest part" *after* the docstrings
have been extracted from the source code by either static or dynamic means.

Terms and definitions:

    logical block:
        a snippet of code that can be executed by itself if given the correct
        global / local variable context.

    PS1:
        The original meaning is "Prompt String 1". For details see:
        [SE32096]_ [BashPS1]_ [CustomPrompt]_ [GeekPrompt]_.  In the context of
        xdoctest, instead of referring to the prompt prefix, we use PS1 to
        refer to a line that starts a "logical block" of code. In the original
        doctest module these all had to be prefixed with ">>>". In xdoctest the
        prefix is used to simply denote the code is part of a doctest. It does
        not necessarily mean a new "logical block" is starting.

    PS2:
        The original meaning is "Prompt String 2". In the context of xdoctest,
        instead of referring to the prompt prefix, we use PS2 to refer to a
        line that continues a "logical block" of code. In the original doctest
        module these all had to be prefixed with "...". However, xdoctest uses
        parsing to automatically determine this.

    want statement:
        Lines directly after a logical block of code in a doctest indicating
        the desired result of executing the previous block.

While I do believe this AST-based code is a significant improvement over the
RE-based builtin doctest parser, I acknowledge that I'm not an AST expert and
there is room for improvement here.


References:
    .. [SE32096] https://unix.stackexchange.com/questions/32096/why-is-bashs-prompt-variable-called-ps1
    .. [BashPS1] https://www.gnu.org/savannah-checkouts/gnu/bash/manual/bash.html#index-PS1
    .. [CustomPrompt] https://wiki.archlinux.org/title/Bash/Prompt_customization
    .. [GeekPrompt] https://web.archive.org/web/20230824025647/https://www.thegeekstuff.com/2008/09/bash-shell-take-control-of-ps1-ps2-ps3-ps4-and-prompt_command/
"""
import ast
import sys
import re
import tokenize
from xdoctest import utils
from xdoctest import directive
from xdoctest import exceptions
from xdoctest import doctest_part
from xdoctest import static_analysis as static
from xdoctest import global_state


INDENT_RE = re.compile(r'^([ ]*)(?=\S)', re.MULTILINE)


class DoctestParser:
    r"""
    Breaks docstrings into parts using the `parse` method.

    Example:
        >>> from xdoctest.parser import *  # NOQA
        >>> parser = DoctestParser()
        >>> doctest_parts = parser.parse(
        >>>     '''
        >>>     >>> j = 0
        >>>     >>> for i in range(10):
        >>>     >>>     j += 1
        >>>     >>> print(j)
        >>>     10
        >>>     '''.lstrip('\n'))
        >>> print('\n'.join(list(map(str, doctest_parts))))
        <DoctestPart(ln 0, src="j = 0...", want=None)>
        <DoctestPart(ln 3, src="print(j)...", want="10...")>

    Example:
        >>> # Having multiline strings in doctests can be nice
        >>> string = utils.codeblock(
                '''
                >>> name = 'name'
                'anything'
                ''')
        >>> self = DoctestParser()
        >>> doctest_parts = self.parse(string)
        >>> print('\n'.join(list(map(str, doctest_parts))))
    """

    def __init__(self, simulate_repl=False):
        """
        Args:
            simulate_repl (bool): if True each line will be treated as its
                own doctest. This more closely mimics the original doctest
                module.  Defaults to False.
        """
        self.simulate_repl = simulate_repl

    def parse(self, string, info=None):
        r"""
        Divide the given string into examples and interleaving text.

        Args:
            string (str): The docstring that may contain one or more doctests.
            info (dict | None): info about where the string came from in case of an
                error

        Returns:
            List[xdoctest.doctest_part.DoctestPart | str]:
                a list of `DoctestPart` objects and intervening text in the
                input docstring.

        CommandLine:
            python -m xdoctest.parser DoctestParser.parse

        Example:
            >>> docstr = '''
            >>>     A simple docstring contains text followed by an example.
            >>>     >>> numbers = [1, 2, 3, 4]
            >>>     >>> thirds = [x / 3 for x in numbers]
            >>>     >>> print(thirds)
            >>>     [0.33  0.66  1  1.33]
            >>> '''
            >>> from xdoctest import parser
            >>> self = parser.DoctestParser()
            >>> results = self.parse(docstr)
            >>> assert len(results) == 3
            >>> for index, result in enumerate(results):
            >>>     print(f'results[{index}] = {result!r}')
            results[0] = '\nA simple docstring contains text followed by an example.'
            results[1] = <DoctestPart(ln 2, src="numbers ...", want=None) at ...>
            results[2] = <DoctestPart(ln 4, src="print(th...", want="[0.33  0...") at ...>

        Example:
            >>> s = 'I am a dummy example with two parts'
            >>> x = 10
            >>> print(s)
            I am a dummy example with two parts
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
            >>> from xdoctest.parser import *  # NOQA
            >>> from xdoctest import parser
            >>> from xdoctest.docstr import docscrape_google
            >>> from xdoctest import core
            >>> self = parser.DoctestParser()
            >>> docstr = self.parse.__doc__
            >>> blocks = docscrape_google.split_google_docblocks(docstr)
            >>> doclineno = self.parse.__func__.__code__.co_firstlineno
            >>> key, (string, offset) = blocks[-2]
            >>> self._label_docsrc_lines(string)
            >>> doctest_parts = self.parse(string)
            >>> # each part with a want-string needs to be broken in two
            >>> assert len(doctest_parts) == 6
            >>> len(doctest_parts)
        """
        if global_state.DEBUG_PARSER > 1:
            print('\n===== PARSE ====')
        if sys.version_info.major == 2:  # nocover
            string = utils.ensure_unicode(string)

        if not isinstance(string, str):
            raise TypeError('Expected string but got {!r}'.format(string))

        # If all lines begin with the same indentation, then strip it.
        min_indent = _min_indentation(string)
        if min_indent > 0:
            string = '\n'.join([ln[min_indent:] for ln in string.splitlines()])

        labeled_lines = None
        grouped_lines = None
        all_parts = None
        try:
            labeled_lines = self._label_docsrc_lines(string)
            grouped_lines = self._group_labeled_lines(labeled_lines)
            all_parts = list(self._package_groups(grouped_lines))
        except Exception as orig_ex:

            if labeled_lines is None:
                failpoint = '_label_docsrc_lines'
            elif grouped_lines is None:
                failpoint = '_group_labeled_lines'
            elif all_parts is None:
                failpoint = '_package_groups'
            if global_state.DEBUG_PARSER:
                print('<FAILPOINT>')
                print('!!! FAILED !!!')
                print('failpoint = {!r}'.format(failpoint))

                import ubelt as ub
                import traceback
                tb_text = traceback.format_exc()
                tb_text = ub.highlight_code(tb_text)
                tb_text = ub.indent(tb_text)
                print(tb_text)

                print('Failed to parse string = <{[<{[<{[  # xdoc debug')
                print(string)
                print(']}>]}>]}>  # xdoc debug end string')

                print('info = {}'.format(ub.repr2(info)))
                print('-----')
                print('orig_ex = {}'.format(orig_ex))
                print('labeled_lines = {}'.format(ub.repr2(labeled_lines)))
                print('grouped_lines = {}'.format(ub.repr2(grouped_lines, nl=3)))
                print('all_parts = {}'.format(ub.repr2(all_parts)))
                print('</FAILPOINT>')
                # sys.exit(1)
            raise exceptions.DoctestParseError(
                'Failed to parse doctest in {}'.format(failpoint),
                string=string, info=info, orig_ex=orig_ex)
        if global_state.DEBUG_PARSER > 1:
            print('\n===== FINISHED PARSE ====')
        return all_parts

    def _package_groups(self, grouped_lines):
        if global_state.DEBUG_PARSER > 1:
            import ubelt as ub
            print('<PACKAGE LABEL GROUPS>')
            print('grouped_lines = {}'.format(ub.repr2(grouped_lines, nl=2)))
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
        if global_state.DEBUG_PARSER > 1:
            print('</PACKAGE LABEL GROUPS>')

    def _package_chunk(self, raw_source_lines, raw_want_lines, lineno=0):
        """
        if `self.simulate_repl` is True, then each statement is broken into its
        own part.  Otherwise, statements are grouped by the closest `want`
        statement.

        TODO:
            - [ ] EXCEPT IN CASES OF EXPLICIT CONTINUATION

        Example:
            >>> from xdoctest.parser import *
            >>> raw_source_lines = ['>>> "string"']
            >>> raw_want_lines = ['string']
            >>> self = DoctestParser()
            >>> part, = self._package_chunk(raw_source_lines, raw_want_lines)
            >>> part.source
            '"string"'
            >>> part.want
            'string'

        """
        if global_state.DEBUG_PARSER > 1:
            print('<PACKAGE CHUNK>')
        match = INDENT_RE.search(raw_source_lines[0])
        line_indent = 0 if match is None else (match.end() - match.start())

        source_lines = [p[line_indent:] for p in raw_source_lines]
        want_lines = [p[line_indent:] for p in raw_want_lines]

        # TODO:
        # - [ ] Fix pytorch indentation issue here

        exec_source_lines = [p[4:] for p in source_lines]

        if global_state.DEBUG_PARSER > 1:
            print(' * locate ps1 lines')
        # Find the line number of each standalone statement
        ps1_linenos, mode_hint = self._locate_ps1_linenos(source_lines)
        if global_state.DEBUG_PARSER > 1:
            print('mode_hint = {!r}'.format(mode_hint))
            print(' * located ps1 lines')
            print(f'ps1_linenos={ps1_linenos}')

        # Find all directives here:
        # A directive necessarily will split a doctest into multiple parts
        # There are two types: block directives and inline-directives
        # * Block directives must exist on their own PS1 line
        # * Block directives insert a breakpoint before
        # * Inline directives may be on a PS1 or PS2 line
        # * Inline directives inserts a breakpoint before and after
        # First find block directives which must exist on there own PS1 line
        break_linenos = []
        ps1_to_directive = {}
        for s1, s2 in zip(ps1_linenos, ps1_linenos[1:] + [None]):
            lines = exec_source_lines[s1:s2]
            directives = list(directive.Directive.extract('\n'.join(lines)))
            if directives:
                ps1_to_directive[s1] = directives
                break_linenos.append(s1)
                if directives[0].inline:
                    if s2 is not None:
                        break_linenos.append(s2)

        if global_state.DEBUG_PARSER > 3:
            print(f'break_linenos={break_linenos}')

        def slice_example(s1, s2, want_lines=None):
            exec_lines = exec_source_lines[s1:s2]
            orig_lines = source_lines[s1:s2]
            directives = ps1_to_directive.get(s1, None)
            example = doctest_part.DoctestPart(exec_lines,
                                               want_lines=want_lines,
                                               orig_lines=orig_lines,
                                               line_offset=lineno + s1,
                                               directives=directives)
            return example

        s1 = 0
        s2 = 0
        if self.simulate_repl:
            # Break down first parts which dont have any want
            for s1, s2 in zip(ps1_linenos, ps1_linenos[1:]):
                example = slice_example(s1, s2)
                yield example
            s1 = s2
        else:
            if break_linenos:
                break_linenos = sorted(set([0] + break_linenos))
                # directives are forcing us to further breakup the parts
                for s1, s2 in zip(break_linenos, break_linenos[1:]):
                    example = slice_example(s1, s2)
                    yield example
                s1 = s2
            if want_lines and mode_hint in {'eval', 'single'}:
                # Whenever the evaluation of the final line needs to be tested
                # against want, that line must be separated into its own part.
                # We break the last line off so we can eval its value, but keep
                # previous groupings.
                s2 = ps1_linenos[-1]
                if s2 != s1:  # make sure the last line is not the only line
                    example = slice_example(s1, s2)
                    yield example
                    s1 = s2
        s2 = None

        example = slice_example(s1, s2, want_lines)

        # if mode_hint is False:
        #     mode_hint = 'exec'
        # if mode_hint is True:
        #     mode_hint = 'eval'

        if not bool(want_lines):
            example.compile_mode = 'exec'
        else:
            assert mode_hint in {'eval', 'exec', 'single'}
            example.compile_mode = mode_hint

        if global_state.DEBUG_PARSER > 1:
            print('example.compile_mode = {!r}'.format(example.compile_mode))
            print('<YIELD CHUNK>')
        yield example

    def _group_labeled_lines(self, labeled_lines):
        """
        Group labeled lines into logical parts to be executed together

        Returns:
            List[List[str] | Tuple[List[str], str]]:
                A list of parts. Text parts are just returned as a list of
                lines.  Executable parts are returned as a tuple of source
                lines and an optional "want" statement.
        """
        if global_state.DEBUG_PARSER > 1:
            print('<GROUP LABEL LINES>')
        # Now that lines have types, groups them. This could have done this
        # above, but functionality is split for readability.
        prev_source = None
        grouped_lines = []

        # WORKON_BACKWARDS_COMPAT_CONTINUE_EVAL
        # Break up explicit continuations for backwards compat
        groups = []
        current = []
        state = None
        if global_state.DEBUG_PARSER > 4:
            print('labeled_lines = {!r}'.format(labeled_lines))

        # Need to ensure that old-style continuations with want statements are
        # placed in their own group, so they can be executed as "single".
        for left, mid, right in _iterthree(labeled_lines, pad_value=(None, None)):
            if left[0] != mid[0] or (mid[0] == 'dsrc' and right[0] == 'dcnt'):
                if not (left[0] == 'dsrc' and mid[0] == 'dcnt'):
                    # Start a new group
                    if state is not None:
                        groups.append((state, current))
                    state = mid[0]
                    current = []
            current.append(mid)
        if current:
            groups.append((state, current))

        if global_state.DEBUG_PARSER > 4:
            print('groups = {!r}'.format(groups))

        # need to merge consecutive dsrc groups without want statements
        merged_groups = []
        current = []
        state = None
        for left, mid, right in _iterthree(groups, pad_value=(None, None)):
            # Merge consecutive groups unless it is followed by a want
            if left[0] == mid[0] and right[0] != 'want':
                # extend the previous group
                current.extend(mid[1])
            else:
                # start a new group
                if state is not None:
                    merged_groups.append((left[0], current))
                state = mid[0]
                current = []
                current.extend(mid[1])
        if current:
            merged_groups.append((state, current))

        # More iterating and grouping. This section needs a careful rewrite
        prev_source = None
        grouped_lines = []
        for state, group in merged_groups:
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
            elif state in {'dsrc', 'dcnt'}:
                if prev_source is not None:
                    # accept a source block without a want block
                    grouped_lines.append((prev_source, ''))
                    prev_source = None
                # need to check if there is a want after us
                prev_source = block
        # Case where last block is source
        if prev_source:
            grouped_lines.append((prev_source, ''))

        if global_state.DEBUG_PARSER > 1:  # nocover
            print('</GROUP LABEL LINES>')
        return grouped_lines

    def _locate_ps1_linenos(self, source_lines):
        """
        Determines which lines in the source begin a "logical block" of code.

        Args:
            source_lines (List[str]): lines belonging only to the doctest src
                these will be unindented, prefixed, and without any want.

        Returns:
            Tuple[List[int], bool]:
                linenos is the first value a list of indices indicating which
                lines are considered "PS1" and
                mode_hint, the second value, is a flag indicating if the final
                line should be considered for a got/want assertion.

        Example:
            >>> self = DoctestParser()
            >>> source_lines = ['>>> def foo():', '>>>     return 0', '>>> 3']
            >>> linenos, mode_hint = self._locate_ps1_linenos(source_lines)
            >>> assert linenos == [0, 2]
            >>> assert mode_hint == 'eval'

        Example:
            >>> from xdoctest.parser import *  # NOQA
            >>> self = DoctestParser()
            >>> source_lines = ['>>> x = [1, 2, ', '>>> 3, 4]', '>>> print(len(x))']
            >>> linenos, mode_hint = self._locate_ps1_linenos(source_lines)
            >>> assert linenos == [0, 2]
            >>> assert mode_hint == 'eval'

        Example:
            >>> from xdoctest.parser import *  # NOQA
            >>> self = DoctestParser()
            >>> source_lines = [
            >>>    '>>> x = 1',
            >>>    '>>> try: raise Exception',
            >>>    '>>> except Exception: pass',
            >>>    '...',
            >>> ]
            >>> linenos, mode_hint = self._locate_ps1_linenos(source_lines)
            >>> assert linenos == [0, 1]
            >>> assert mode_hint == 'exec'

        Example:
            >>> from xdoctest.parser import *  # NOQA
            >>> self = DoctestParser()
            >>> source_lines = [
            >>>    '>>> import os; print(os)',
            >>>    '...',
            >>> ]
            >>> linenos, mode_hint = self._locate_ps1_linenos(source_lines)
            >>> assert linenos == [0]
            >>> assert mode_hint == 'single'

        Example:
            >>> # We should ensure that decorators are PS1 lines
            >>> from xdoctest.parser import *  # NOQA
            >>> self = DoctestParser()
            >>> source_lines = [
            >>>    '>>> # foo',
            >>>    '>>> @foo',
            >>>    '... def bar():',
            >>>    '...     ...',
            >>> ]
            >>> linenos, mode_hint = self._locate_ps1_linenos(source_lines)
            >>> print(f'linenos={linenos}')
            >>> assert linenos == [0, 1]
        """
        # Strip indentation (and PS1 / PS2 from source)
        exec_source_lines = [p[4:] for p in source_lines]

        def _hack_comment_statements(lines):
            # Hack to make comments appear like executable statements
            # note, this hack never leaves this function because we only are
            # returning line numbers.
            # FIXME: there is probably a better way to do this.
            def balanced_intervals(lines):
                """
                Finds intervals of balanced nesting syntax

                Args:
                    lines (List[str]): lines of source code
                """
                intervals = []
                a = len(lines) - 1
                b = len(lines)
                while b > 0:
                    # move the head pointer up until we become balanced
                    while not static.is_balanced_statement(lines[a:b], only_tokens=True) and a >= 0:
                        a -= 1
                    if a < 0:
                        raise exceptions.IncompleteParseError(
                            'ill-formed doctest: cannot find balanced ps1 lines.')
                    # we found a balanced interval
                    intervals.append((a, b))
                    b = a
                    a = a - 1

                intervals = intervals[::-1]
                return intervals
            intervals = balanced_intervals(lines)
            interval_starts = {t[0] for t in intervals}
            for i, line in enumerate(lines):
                if i in interval_starts and line.startswith('#'):
                    # Replace any comment that is not within an interval with a
                    # statement, so ast.parse will record its line number
                    yield '_._ = None'
                else:
                    yield line

        exec_source_lines = list(_hack_comment_statements(exec_source_lines))

        source_block = '\n'.join(exec_source_lines)
        try:
            pt = static.six_axt_parse(source_block)
        except SyntaxError as syn_ex:
            # Assign missing information to the syntax error.
            if syn_ex.text is None:
                if syn_ex.lineno is not None:
                    # Grab the line where the error occurs
                    # (why is this not populated in SyntaxError by default?)
                    # (because filename does not point to a valid loc)
                    line = source_block.split('\n')[syn_ex.lineno - 1]
                    syn_ex.text = line  + '\n'
            raise syn_ex

        # print(ast.dump(pt))
        # print('pt = {!r}'.format(pt))

        statement_nodes = pt.body
        ps1_linenos = [node.lineno - 1 for node in statement_nodes]

        if 1:
            # Get PS1 line numbers of statements accounting for decorators
            ps1_linenos = []
            for node in statement_nodes:
                if hasattr(node, 'decorator_list') and node.decorator_list:
                    lineno = node.decorator_list[0].lineno - 1
                else:
                    lineno = node.lineno - 1
                ps1_linenos.append(lineno)

        # Respect any line explicitly defined as PS2 (via its prefix)
        ps2_linenos = {
            x for x, p in enumerate(source_lines) if p[:4] != '>>> '
        }
        ps1_linenos = sorted(set(ps1_linenos).difference(ps2_linenos))

        # There are 3 ways to compile python code
        # exec, eval, and single.

        # We almost always want to exec, but if we want to match the return
        # value of the function, we will need to run it in eval or single mode.
        mode_hint = 'exec'
        if len(statement_nodes) == 0:
            mode_hint = 'exec'
        else:
            # Is the last statement evaluate-able?
            if isinstance(statement_nodes[-1], ast.Expr):
                # This should just be an Expr in python3
                # (todo: ensure this is true)
                mode_hint = 'eval'

        # WORKON_BACKWARDS_COMPAT_CONTINUE_EVAL:
        # Force doctests parts to evaluate in backwards compatible "single"
        # mode when using old style doctest syntax.
        if len(source_lines) > 1:
            if source_lines[0].startswith('>>> '):
                if all(_hasprefix(s, ('...',)) for s in source_lines[1:]):
                    mode_hint = 'single'

        if mode_hint == 'eval':
            # Also check the tokens in the source lines to look for semicolons
            # to fix #108
            # Only iterate through non-empty lines otherwise tokenize will stop short
            # TODO: we probably could just save the tokens if we got them earlier?
            iterable = (line for line in exec_source_lines if line)
            def _readline():
                return next(iterable)
            # We cannot eval a statement with a semicolon in it
            # Single should work.
            if any(t.type == tokenize.OP and t.string == ';'
                   for t in tokenize.generate_tokens(_readline)):
                mode_hint = 'single'

        return ps1_linenos, mode_hint

    def _label_docsrc_lines(self, string):
        """
        Give each line in the docstring a label so we can distinguish
        what parts are text, what parts are code, and what parts are "want"
        string.

        Args:
            string (str): doctest source

        Returns:
            List[Tuple[str, str]]: labeled_lines - the above source broken
                up by lines, each with a label indicating its type for later
                use in parsing.

        TODO:
            - [ ] Sphinx does not parse this doctest properly

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
            >>> labeled = self._label_docsrc_lines(string)
            >>> expected = [
            >>>     ('text', 'text'),
            >>>     ('dsrc', ">>> items = ['also', 'nice', 'to', 'not', 'worry',"),
            >>>     ('dsrc', ">>>          'about', '...', 'vs', '>>>']"),
            >>>     ('dcnt', "... print('but its still allowed')"),
            >>>     ('want', 'but its still allowed'),
            >>>     ('text', ''),
            >>>     ('text', 'more text')
            >>> ]
            >>> assert labeled == expected
        """

        # parse and differentiate between doctest source and want statements.
        labeled_lines = []
        state_indent = 0

        # line states
        TEXT = 'text'
        DSRC = 'dsrc'
        DCNT = 'dcnt'  # explicit continuation  **new in 0.10.0**
        WANT = 'want'

        # Move through states, keeping track of points where states change
        #     text -> [text, dsrc]
        #     dsrc -> [dsrc, dcnt, want, text]
        #     dcnt -> [dsrc, dcnt, want, text]
        #     want -> [want, text, dsrc]
        prev_state = TEXT
        curr_state = None
        line_iter = enumerate(string.splitlines())

        for line_idx, line in line_iter:
            match = INDENT_RE.search(line)
            line_indent = 0 if match is None else (match.end() - match.start())
            if global_state.DEBUG_PARSER:  # nocover
                print('Next line {}: {}'.format(line_idx, line))
                print('state_indent = {!r}'.format(state_indent))
                print('match = {!r}'.format(match))
                print('line_indent = {!r}'.format(line_indent))

            norm_line = line[state_indent:]  # Normalize line indentation
            strip_line = line.strip()

            # Check prev_state transitions
            if prev_state == TEXT:
                # text transitions to source whenever a PS1 line is encountered
                # the PS1(>>>) can be at an arbitrary indentation
                if _hasprefix(strip_line, ('>>>',)):
                    curr_state = DSRC
                else:
                    curr_state = TEXT
            elif prev_state == WANT:
                # blank lines terminate wants
                if len(strip_line) == 0:
                    curr_state = TEXT
                # source-inconsistent indentation terminates want
                elif _hasprefix(line.strip(), ('>>>',)):
                    curr_state = DSRC
                elif line_indent < state_indent:
                    curr_state = TEXT
                else:
                    curr_state = WANT
            elif prev_state in {DSRC, DCNT}:  # pragma: nobranch
                if len(strip_line) == 0 or line_indent < state_indent:
                    curr_state = TEXT
                # allow source to continue with either PS1 or PS2
                elif _hasprefix(norm_line, ('>>>', '...')):
                    if strip_line == '...':
                        # TODO: add mechanism for checking next line.
                        # if the next line is also a continuation
                        # then dont treat this as an ellipses
                        if prev_state == DCNT:
                            # Hack to fix continuation issue
                            curr_state = DCNT
                        else:
                            curr_state = WANT
                    else:
                        if _hasprefix(norm_line, ('...',)):
                            curr_state = DCNT
                        else:
                            curr_state = DSRC
                else:
                    curr_state = WANT
            else:  # nocover
                # This should never happen
                raise AssertionError('Unknown state prev_state={}'.format(
                    prev_state))

            # Handle transitions
            if prev_state != curr_state:
                # Handle start of new states
                if curr_state == TEXT:
                    state_indent = 0
                if curr_state in {DSRC, DCNT}:
                    # Start a new source
                    state_indent = line_indent
                    # renormalize line when indentation changes
                    norm_line = line[state_indent:]

            # continue current state
            if curr_state in {DSRC, DCNT}:
                # source parts may consume more than one line
                try:
                    if global_state.DEBUG_PARSER:  # nocover
                        print('completing source')
                    for part, norm_line in _complete_source(line, state_indent, line_iter):
                        if global_state.DEBUG_PARSER > 4:  # nocover
                            print('Append Completion Line:')
                            print('part = {!r}'.format(part))
                            print('norm_line = {!r}'.format(norm_line))
                            print('curr_state = {!r}'.format(curr_state))
                        if _hasprefix(norm_line, ('...',)):
                            curr_state = DCNT
                        labeled_lines.append((curr_state, part))

                except exceptions.IncompleteParseError:
                    raise
                except SyntaxError:
                    if global_state.DEBUG_PARSER:  # nocover
                        print('<LABEL FAIL>')
                        # print('next(line_iter) = {!r}'.format(line_iter))
                        print('state_indent = {!r}'.format(state_indent))
                        print('line = {!r}'.format(line))
                        print('Failed to label source lines')
                        print('Labeled lines so far: <[[[[[[[[[[')
                        for line in labeled_lines:
                            print(line)
                        print(']]]]]]]]]]>')
                        print('</LABEL FAIL>')
                    raise
            elif curr_state == WANT:
                labeled_lines.append((curr_state, line))
            elif curr_state == TEXT:
                labeled_lines.append((curr_state, line))
            prev_state = curr_state

        if global_state.DEBUG_PARSER > 1:  # nocover
            import ubelt as ub
            # if global_state.DEBUG_PARSER > 3:
            #     print('string = {!r}'.format(string))
            print('<FINISH LABELED LINES')
            print('labeled_lines = {}'.format(ub.repr2(labeled_lines, nl=1)))
            print('</FINISH LABELED LINES>')

        return labeled_lines


def _min_indentation(s):
    "Return the minimum indentation of any non-blank line in `s`"
    indents = [len(indent) for indent in INDENT_RE.findall(s)]
    if len(indents) > 0:
        return min(indents)
    else:
        return 0


def _complete_source(line, state_indent, line_iter):
    """
    helper
    remove lines from the iterator if they are needed to complete source

    This uses :func:`static.is_balanced_statement` to do the heavy lifting

    Example:
        >>> from xdoctest.parser import *  # NOQA
        >>> from xdoctest.parser import _complete_source
        >>> state_indent = 0
        >>> line = '>>> x = { # The line is not finished'
        >>> remain_lines = ['>>> 1:2,', '>>> 3:4,', '>>> 5:6}', '>>> y = 7']
        >>> line_iter = enumerate(remain_lines, start=1)
        >>> finished = list(_complete_source(line, state_indent, line_iter))
        >>> final = chr(10).join([t[1] for t in finished])
        >>> print(final)
    """
    norm_line = line[state_indent:]  # Normalize line indentation
    prefix = norm_line[:4]
    suffix = norm_line[4:]
    assert prefix.strip() in {'>>>', '...'}, (
        'unexpected prefix: {!r}'.format(prefix))
    yield line, norm_line

    source_parts = [suffix]

    # These hacks actually modify the input doctest slightly
    HACK_TRIPLE_QUOTE_FIX = True

    try:
        while not static.is_balanced_statement(source_parts, only_tokens=True):
            line_idx, next_line = next(line_iter)
            norm_line = next_line[state_indent:]
            prefix = norm_line[:4]
            suffix = norm_line[4:]

            if prefix.strip() not in {'>>>', '...', ''}:  # nocover
                error = True
                if HACK_TRIPLE_QUOTE_FIX:
                    # TODO: make a more robust patch
                    if any("'''" in s or '"""' in s for s in source_parts):
                        # print('HACK FIXING TRIPLE QUOTE')
                        next_line = next_line[:state_indent] + '... ' + norm_line
                        norm_line = '... ' + norm_line
                        prefix = ''
                        suffix = norm_line
                        error = False

                if error:
                    if global_state.DEBUG_PARSER:
                        print(' * !!!ERROR!!!')
                        print(' * source_parts = {!r}'.format(source_parts))
                        print(' * prefix = {!r}'.format(prefix))
                        print(' * norm_line = {!r}'.format(norm_line))
                        print(' * !!!!!!!!!!!!!')

                    raise SyntaxError(
                        'Bad indentation in doctest on line {}: {!r}'.format(
                            line_idx, next_line))
            source_parts.append(suffix)
            yield next_line, norm_line
    except StopIteration:
        if global_state.DEBUG_PARSER:
            import ubelt as ub
            print('<FAIL DID NOT COMPLETE SOURCE>')
            import traceback
            tb_text = traceback.format_exc()
            tb_text = ub.highlight_code(tb_text)
            tb_text = ub.indent(tb_text)
            print(tb_text)
            # print(' * line_iter = {!r}'.format(line_iter))
            print(' * state_indent = {!r}'.format(state_indent))
            print(' * line = {!r}'.format(line))
            # print('source =\n{}'.format('\n'.join(source_parts)))
            print('# Ensure that the following line should actually fail')
            print('source_parts = {}'.format(ub.repr2(source_parts, nl=2)))
            print(ub.codeblock(
                r'''
                from xdoctest import static_analysis as static
                static.is_balanced_statement(source_parts, only_tokens=False)
                static.is_balanced_statement(source_parts, only_tokens=True)
                text = '\n'.join(source_parts)
                print(text)
                static.six_axt_parse(text)
                '''))
            print('</FAIL DID NOT COMPLETE SOURCE>')
            # sys.exit(1)
        # TODO: use AST to reparse all doctest parts to discover where the
        # syntax error in the doctest is and then raise it.
        raise exceptions.IncompleteParseError(
            'ill-formed doctest: all parts have been processed '
            'but the doctest source is not balanced')
    else:
        if global_state.DEBUG_PARSER > 1:
            import ubelt as ub
            print('<SUCCESS COMPLETED SOURCE>')
            # print(' * line_iter = {!r}'.format(line_iter))
            print('source_parts = {}'.format(ub.repr2(source_parts, nl=2)))
            print('</SUCCESS COMPLETED SOURCE>')


def _iterthree(items, pad_value=None):
    """
    Iterate over a sliding window of size 3 with None padding on
    both sides.

    Example:
        >>> from xdoctest.parser import *
        >>> print(list(_iterthree([])))
        >>> print(list(_iterthree(range(1))))
        >>> print(list(_iterthree([1, 2])))
        >>> print(list(_iterthree([1, 2, 3])))
        >>> print(list(_iterthree(range(4))))
        >>> print(list(_iterthree(range(7))))
    """
    # Initialize the return window to pad values
    left = mid = right = pad_value
    # Create an iterator
    item_iter = iter(items)
    # Check the first item, if we dont have it, then dont return anything
    try:
        mid = next(item_iter)
    except StopIteration:
        return
    else:
        # Check the second item, if we dont have it, we have to return
        # the values we've seen so far.
        try:
            right = next(item_iter)
        except StopIteration:
            yield left, mid, right
            return
        else:
            # If we have both mid and right, then yield both
            yield left, mid, right
            left, mid = mid, right
            # If there is still data
            for right in item_iter:
                yield left, mid, right
                left, mid = mid, right
        right = pad_value
        yield left, mid, right


def _hasprefix(line, prefixes):
    """ helper prefix test """
    # if not isinstance(prefixes, tuple):
    #     prefixes = [prefixes]
    return any(line == p or line.startswith(p + ' ') for p in prefixes)


if __name__ == '__main__':
    """
    CommandLine:
        python -m xdoctest.core
        python -m xdoctest.parser all
    """
    import xdoctest as xdoc
    xdoc.doctest_module()

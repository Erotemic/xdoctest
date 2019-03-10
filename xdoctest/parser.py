# -*- coding: utf-8 -*-
"""
Terms and definitions:

    logical block: a snippet of code that can be executed by itself if given
        the correct global / local variable context.

    PS1 : The original meaning is "Prompt String 1". In the context of
        xdoctest, instead of referring to the prompt prefix, we use PS1 to refer
        to a line that starts a "logical block" of code. In the original
        doctest module these all had to be prefixed with ">>>". In xdoctest the
        prefix is used to simply denote the code is part of a doctest. It does
        not necessarilly mean a new "logical block" is starting.

    PS2 : The original meaning is "Prompt String 2". In the context of
        xdoctest, instead of referring to the prompt prefix, we use PS2 to refer
        to a line that continues a "logical block" of code. In the original
        doctest module these all had to be prefixed with "...". However,
        xdoctest uses parsing to automatically determine this.

    want statement: Lines directly after a logical block of code in a doctest
        indicating the desired result of executing the previous block.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import six
import ast
import sys
import re
import itertools as it
from xdoctest import utils
from xdoctest import checker
from xdoctest import directive
from xdoctest import exceptions
from xdoctest import doctest_part
from xdoctest import static_analysis as static


class IncompleteParseError(SyntaxError):
    pass


DEBUG = 0


GotWantException = checker.GotWantException


INDENT_RE = re.compile(r'^([ ]*)(?=\S)', re.MULTILINE)


class DoctestParser(object):
    r"""
    Breaks docstrings into parts using the `parse` method.

    Example:
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
    """

    def __init__(self, simulate_repl=False):
        self.simulate_repl = simulate_repl

    def parse(self, string, info=None):
        """
        Divide the given string into examples and interleaving text.

        Args:
            string (str): string representing the doctest
            info (dict): info about where the string came from in case of an
                error

        Returns:
            list : a list of `DoctestPart` objects

        CommandLine:
            python -m xdoctest.parser DoctestParser.parse

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
        """
        if DEBUG > 1:
            print('\n===== PARSE ====')
        if sys.version_info.major == 2:  # nocover
            string = utils.ensure_unicode(string)

        if not isinstance(string, six.string_types):
            raise TypeError('Expected string but got {!r}'.format(string))

        string = string.expandtabs()
        # If all lines begin with the same indentation, then strip it.
        min_indent = min_indentation(string)
        if min_indent > 0:
            string = '\n'.join([l[min_indent:] for l in string.splitlines()])

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
            if DEBUG:
                print('<FAILPOINT>')
                print('!!! FAILED !!!')
                print('failpoint = {!r}'.format(failpoint))

                import ubelt as ub
                import traceback
                tb_text = traceback.format_exc()
                tb_text = ub.highlight_code(tb_text)
                tb_text = ub.indent(tb_text)
                print(tb_text)

                print('Failed to parse string = <<<<<<<<<<<')
                print(string)
                print('>>>>>>>>>>>  # end string')

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
        if DEBUG > 1:
            print('\n===== FINISHED PARSE ====')
        return all_parts

    def _package_groups(self, grouped_lines):
        if DEBUG > 1:
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
        if DEBUG > 1:
            print('</PACKAGE LABEL GROUPS>')

    def _package_chunk(self, raw_source_lines, raw_want_lines, lineno=0):
        """
        if `self.simulate_repl` is True, then each statement is broken into its
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
            'string'

        """
        if DEBUG > 1:
            print('<PACKAGE CHUNK>')
        match = INDENT_RE.search(raw_source_lines[0])
        line_indent = 0 if match is None else (match.end() - match.start())

        source_lines = [p[line_indent:] for p in raw_source_lines]
        want_lines = [p[line_indent:] for p in raw_want_lines]

        # TODO:
        # - [ ] Fix pytorch indentation issue here

        exec_source_lines = [p[4:] for p in source_lines]

        if DEBUG > 1:
            print(' * locate ps1 lines')
        # Find the line number of each standalone statement
        ps1_linenos, eval_final = self._locate_ps1_linenos(source_lines)
        if DEBUG > 1:
            print(' * located ps1 lines')

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
            if want_lines and eval_final:
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
        example.use_eval = bool(want_lines) and eval_final
        # example.use_eval = eval_final
        if DEBUG > 1:
            print('<YIELD CHUNK>')
        yield example

    def _group_labeled_lines(self, labeled_lines):
        if DEBUG > 1:
            print('<GROUP LABEL LINES>')
        # Now that lines have types, group them. This could have done this
        # above, but functionality is split for readability.
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
        if DEBUG > 1:
            print('</GROUP LABEL LINES>')
        return grouped_lines

    def _locate_ps1_linenos(self, source_lines):
        """
        Determines which lines in the source begin a "logical block" of code.

        Args:
            source_lines (list): lines belonging only to the doctest src
                these will be unindented, prefixed, and without any want.

        Returns:
            (list, bool): a list of indices indicating which lines
               are considered "PS1" and a flag indicating if the final line
               should be considered for a got/want assertion.

        Example:
            >>> self = DoctestParser()
            >>> source_lines = ['>>> def foo():', '>>>     return 0', '>>> 3']
            >>> linenos, eval_final = self._locate_ps1_linenos(source_lines)
            >>> assert linenos == [0, 2]
            >>> assert eval_final is True

        Example:
            >>> self = DoctestParser()
            >>> source_lines = ['>>> x = [1, 2, ', '>>> 3, 4]', '>>> print(len(x))']
            >>> linenos, eval_final = self._locate_ps1_linenos(source_lines)
            >>> assert linenos == [0, 2]
            >>> assert eval_final is True
        """
        # print('source_lines = {!r}'.format(source_lines))
        # Strip indentation (and PS1 / PS2 from source)
        exec_source_lines = [p[4:] for p in source_lines]
        # print('\n'.join(exec_source_lines))

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
                    while not static.is_balanced_statement(lines[a:b], only_tokens=True):
                        a -= 1
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

        statement_nodes = pt.body
        ps1_linenos = [node.lineno - 1 for node in statement_nodes]
        NEED_16806_WORKAROUND = True
        if NEED_16806_WORKAROUND:  # pragma: nobranch
            ps1_linenos = self._workaround_16806(
                ps1_linenos, exec_source_lines)

        # Respect any line explicitly defined as PS2 (via its prefix)
        ps2_linenos = {
            x for x, p in enumerate(source_lines) if p[:4] != '>>> '
        }
        ps1_linenos = sorted(set(ps1_linenos).difference(ps2_linenos))

        if len(statement_nodes) == 0:
            eval_final = False
        else:
            # Is the last statement evaluate-able?
            if sys.version_info.major == 2:  # nocover
                eval_final = isinstance(statement_nodes[-1], (
                    ast.Expr, ast.Print))
            else:
                # This should just be an Expr in python3
                # (todo: ensure this is true)
                eval_final = isinstance(statement_nodes[-1], ast.Expr)

        return ps1_linenos, eval_final

    @staticmethod
    def _workaround_16806(ps1_linenos, exec_source_lines):
        """
        workaround for python issue 16806 (https://bugs.python.org/issue16806)

        This issue causes the AST to report line numbers for multiline strings
        as the line they end on. The correct behavior is to report the line
        they start on. Given a list of line numbers and the original source
        code, this workaround fixes any line number that points from the end of
        a multiline string to point to the start of it instead.

        Args:
            ps1_linenos (List[int]): AST provided line numbers that begin
                statements and may be Python Issue #16806.
            exec_source_lines (List[str]): code referenced by ps1_linenos

        Returns:
            List[int]: new_ps1_lines: Fixed `ps1_linenos` where multiline
                strings now point to the line where they begin.

        Notes:
            A patch for this issue exists
            `https://github.com/python/cpython/pull/1800`. This workaround is a
            no-op when the line numbers are correct, so nothing should break
            when this bug is fixed.

            Starting from the end look at consecutive pairs of indices to
            inspect the statement it corresponds to.  (the first statement goes
            from ps1_linenos[-1] to the end of the line list.

        Example:
            >>> ps1_linenos = [0, 2, 3]
            >>> exec_source_lines = ["x = 1", "y = '''foo", " bar'''", "pass"]
            >>> DoctestParser._workaround_16806(ps1_linenos, exec_source_lines)
            [0, 1, 3]
        """
        new_ps1_lines = []
        b = len(exec_source_lines)
        for a in ps1_linenos[::-1]:
            # the position of `b` is correct, but `a` may be wrong
            # is_balanced_statement will be False iff `a` is wrong.
            while not static.is_balanced_statement(exec_source_lines[a:b], only_tokens=True):
                # shift `a` down until it becomes correct
                a -= 1
            # push the new correct value back into the list
            new_ps1_lines.append(a)
            # set the end position of the next string to be `a` , note, because
            # this `a` is correct, the next `b` is must also be correct.
            b = a
        return new_ps1_lines[::-1]

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
            >>> labeled = self._label_docsrc_lines(string)
            >>> expected = [
            >>>     ('text', 'text'),
            >>>     ('dsrc', ">>> items = ['also', 'nice', 'to', 'not', 'worry',"),
            >>>     ('dsrc', ">>>          'about', '...', 'vs', '>>>']"),
            >>>     ('dsrc', "... print('but its still allowed')"),
            >>>     ('want', 'but its still allowed'),
            >>>     ('text', ''),
            >>>     ('text', 'more text')
            >>> ]
            >>> assert labeled == expected
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

            # These hacks actually modify the input doctest slighly
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
                            if DEBUG:
                                print(' * !!!ERROR!!!')
                                print(' * source_parts = {!r}'.format(source_parts))
                                print(' * prefix = {!r}'.format(prefix))
                                print(' * norm_line = {!r}'.format(norm_line))
                                print(' * !!!!!!!!!!!!!')

                            raise SyntaxError(
                                'Bad indentation in doctest on line {}: {!r}'.format(
                                    line_idx, next_line))
                    source_parts.append(suffix)
                    yield next_line
            except StopIteration:
                if DEBUG:
                    import ubelt as ub
                    print('<FAIL DID NOT COMPLETE SOURCE>')
                    import traceback
                    tb_text = traceback.format_exc()
                    tb_text = ub.highlight_code(tb_text)
                    tb_text = ub.indent(tb_text)
                    print(tb_text)
                    print(' * line_iter = {!r}'.format(line_iter))
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
                # TODO: use AST to reparse all doctest parts to discover
                # where the syntax error in the doctest is and then raise
                # it.
                raise IncompleteParseError(
                    'ill-formed doctest: all parts have been processed '
                    'but the doctest source is not balanced')
            else:
                if DEBUG > 1:
                    import ubelt as ub
                    print('<SUCCESS COMPLETED SOURCE>')
                    print(' * line_iter = {!r}'.format(line_iter))
                    print('source_parts = {}'.format(ub.repr2(source_parts, nl=2)))
                    print('</SUCCESS COMPLETED SOURCE>')

        # parse and differentiate between doctest source and want statements.
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

        def hasprefix(line, prefixes):
            if not isinstance(prefixes, tuple):
                prefixes = [prefixes]
            return any(line == p or line.startswith(p + ' ') for p in prefixes)

        for line_idx, line in line_iter:
            match = INDENT_RE.search(line)
            line_indent = 0 if match is None else (match.end() - match.start())
            norm_line = line[state_indent:]  # Normalize line indentation
            strip_line = line.strip()

            # Check prev_state transitions
            if prev_state == TEXT:
                # text transitions to source whenever a PS1 line is encountered
                # the PS1(>>>) can be at an arbitrary indentation
                if hasprefix(strip_line, '>>>'):
                    curr_state = DSRC
                else:
                    curr_state = TEXT
            elif prev_state == WANT:
                # blank lines terminate wants
                if len(strip_line) == 0:
                    curr_state = TEXT
                # source-inconsistent indentation terminates want
                elif hasprefix(line.strip(), '>>>'):
                    curr_state = DSRC
                elif line_indent < state_indent:
                    curr_state = TEXT
                else:
                    curr_state = WANT
            elif prev_state == DSRC:  # pragma: nobranch
                if len(strip_line) == 0 or line_indent < state_indent:
                    curr_state = TEXT
                # allow source to continue with either PS1 or PS2
                elif hasprefix(norm_line, ('>>>', '...')):
                    if strip_line == '...':
                        curr_state = WANT
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
                if curr_state == DSRC:
                    # Start a new source
                    state_indent = line_indent
                    # renormalize line when indentation changes
                    norm_line = line[state_indent:]

            # continue current state
            if curr_state == DSRC:
                # source parts may consume more than one line
                try:
                    for part in _complete_source(line, state_indent, line_iter):
                        labeled_lines.append((DSRC, part))
                except IncompleteParseError as orig_ex:
                    raise
                except SyntaxError as orig_ex:
                    if DEBUG:
                        print('<LABEL FAIL>')
                        print('line_iter = {!r}'.format(line_iter))
                        # print('next(line_iter) = {!r}'.format(line_iter))
                        print('state_indent = {!r}'.format(state_indent))
                        print('line = {!r}'.format(line))
                        print('Failed to label source lines')
                        print('Labeled lines so far: <<<<<<<<<<<')
                        for line in labeled_lines:
                            print(line)
                        print('>>>>>>>>>>>')
                        print('</LABEL FAIL>')
                    raise
            elif curr_state == WANT:
                labeled_lines.append((WANT, line))
            elif curr_state == TEXT:
                labeled_lines.append((TEXT, line))
            prev_state = curr_state

        if DEBUG > 1:
            import ubelt as ub
            print('<FINISH LABELED LINES')
            print('labeled_lines = {}'.format(ub.repr2(labeled_lines, nl=1)))
            print('</FINISH LABELED LINES>')

        return labeled_lines


def min_indentation(s):
    "Return the minimum indentation of any non-blank line in `s`"
    indents = [len(indent) for indent in INDENT_RE.findall(s)]
    if len(indents) > 0:
        return min(indents)
    else:
        return 0


if __name__ == '__main__':
    """
    CommandLine:
        python -m xdoctest.core
        python -m xdoctest.parser all
    """
    import xdoctest as xdoc
    xdoc.doctest_module()

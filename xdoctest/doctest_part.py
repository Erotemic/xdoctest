# -*- coding: utf-8 -*-
"""
Simple storage container used to store a single executable part of a doctest
example. Multiple parts are typically stored in a
:class:`xdoctest.doctest_example.Doctest`, which manages execution of each
part.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import math
from xdoctest import utils
from xdoctest import checker
from xdoctest import directive
from xdoctest import constants


__devnotes__ = """
TODO:
    perhaps rename doctest part to DoctestCell, because there is a striking
    similarity between Jupyter notebook cells and doctest parts.
"""


class DoctestPart(object):
    """
    The result of parsing that represents a "logical block" of code.
    If a want statment is defined, it is stored here.

    Attributes:
        exec_lines (list): executable lines in this part
        want_lines (list): lines that the result of the execution should match
        line_offset (int): line number relative to the start of the doctest
        orig_lines (list): the original text parsed into exec and want
        _directives (list): directives that this part will apply before being run
        partno (int): identifies the part number in the larger example
        compile_mode (str): mode passed to compile.
    """
    def __init__(self, exec_lines, want_lines=None, line_offset=0,
                 orig_lines=None, directives=None, partno=None):
        self.exec_lines = exec_lines
        self.want_lines = want_lines
        self.line_offset = line_offset
        self.orig_lines = orig_lines
        self.compile_mode = 'exec'
        self._directives = directives
        self.partno = partno

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
    def directives(self):
        """
        CommandLine:
            python -m xdoctest.parser DoctestPart.directives

        Example:
            >>> self = DoctestPart(['# doctest: +SKIP'], None, 0)
            >>> print(', '.join(list(map(str, self.directives))))
            <Directive(+SKIP)>
        """
        if self._directives is None:
            self._directives = list(directive.Directive.extract(self.source))
        return self._directives

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
        if self.source:
            head_src = self.source.splitlines()[0][0:8]
            parts.append('src="%s..."' % (head_src,))
        else:
            parts.append('src=""')

        if self.want is None:
            parts.append('want=None')
        else:
            head_wnt = self.want.splitlines()[0][0:8]
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

    def check(part, got_stdout, got_eval=constants.NOT_EVALED, runstate=None,
              unmatched=None):
        r"""
        Check if the "got" output obtained by running this test matches the
        "want" target. Note there are two types of "got" output: (1) output
        from stdout and (2) evaled output. If both are specified, then want may
        match either value.

        Args:
            got_stdout (str): output from stdout
            got_eval (str): output from an eval statement
            runstate (directive.RuntimeState): runner options
            unmatched (list): if specified, the want statement is allowed
                to match any trailing sequence of unmatched output and
                got_stdout from this doctest part.

        Raises:
            xdoctest.checker.GotWantException - If the "got" differs from this
                parts want.

        Example:
            >>> # xdoctest: +REQUIRES(module:pytest)
            >>> import pytest
            >>> got_stdout = 'more text\n'
            >>> unmatched = ['some text\n']
            >>> self = DoctestPart(None, want_lines=['some text', 'more text'])
            >>> self.check(got_stdout, unmatched=unmatched)
            >>> # Leading junk doesnt matter if we match a trailing sequence
            >>> self.check(got_stdout, unmatched=['junk\n'] + unmatched)
            >>> # fail when want doesnt match any trailing sequence
            >>> with pytest.raises(checker.GotWantException):
            >>>     self.check(got_stdout)
            >>> with pytest.raises(checker.GotWantException):
            >>>     self.check(got_stdout, ['some text\n', 'junk\n'])
        """
        if unmatched is None:
            unmatched = []
        trailing_gots = unmatched + [got_stdout]
        success = False

        exceptions = []
        for i in range(1, len(trailing_gots) + 1):
            # Try the i-th trailing sequence
            got_ = ''.join(trailing_gots[-i:])
            try:
                checker.check_got_vs_want(part.want, got_, got_eval, runstate)
            except checker.GotWantException as ex:
                exceptions.append(ex)
            else:
                success = True
                break

        if not success:
            # for ex in exceptions:
            #     print(ex.output_difference())
            #     print(ex.output_repr_difference())
            # If none of the checks pass, return the error message with the
            # largets got message. (perhaps the output with the closest edit
            # distance might be better to report?)
            raise exceptions[-1]

    def format_part(self, linenos=True, want=True, startline=1, n_digits=None,
                    colored=False, partnos=False, prefix=True):
        """
        Customizable formatting of the source and want for this doctest.

        CommandLine:
            python -m xdoctest.doctest_part DoctestPart.format_part

        Args:
            linenos (bool): show line numbers
            want (bool): include the want value if it exists
            startline (int): offsets the line numbering
            n_digits (int): number of digits to use for line numbers
            colored (bool): pygmentize the colde
            partnos (bool): if True, shows the part number in the string
            prefix (bool): if False, exclude the doctest `>>> ` prefix

        CommandLine:
            python -m xdoctest.doctest_part DoctestPart.format_part:0

        Example:
            >>> from xdoctest.parser import *
            >>> self = DoctestPart(exec_lines=['print(123)'],
            >>>                    want_lines=['123'], line_offset=0, partno=1)
            >>> # xdoctest: -NORMALIZE_WHITESPACE
            >>> print(self.format_part(partnos=True))
            (p1) 1 >>> print(123)
                   123

        Example:
            >>> from xdoctest.parser import *
            >>> self = DoctestPart(exec_lines=['print(123)'],
            >>>                    want_lines=['123'], line_offset=0, partno=1)
            >>> # xdoctest: -NORMALIZE_WHITESPACE
            >>> print(self.format_part(partnos=False, prefix=False,
            >>>                       linenos=False, want=False))
            print(123)
        """
        if prefix:
            # Show the original line prefix when possible
            if self.orig_lines is None:
                src_text = utils.indent(self.source, '>>> ')
            else:
                src_text = '\n'.join(self.orig_lines)
        else:
            src_text = self.source

        want_text = self.want if self.want else ''

        if n_digits is None:
            endline = startline + self.n_lines
            n_digits = math.log(max(1, endline), 10)
            n_digits = int(math.ceil(n_digits))

        part_lines = src_text.splitlines()
        n_spaces = 0

        if linenos:
            n_spaces += n_digits + 1
            start = startline + self.line_offset
            part_lines = utils.add_line_numbers(part_lines, n_digits=n_digits,
                                                start=start)

        if partnos:
            part_lines = [
                '(p{}) {}'.format(self.partno, line)
                for line in part_lines
            ]
            n_spaces += 4 + 1  # FIXME could be more robust if more than 9 parts

        want_lines = []
        if want_text:
            want_fmt = ' ' * n_spaces + '{line}'
            for line in want_text.splitlines():
                if want:
                    want_lines.append(want_fmt.format(line=line))

        part_text = '\n'.join(part_lines)
        want_text = '\n'.join(want_lines)

        if colored:
            part_text = utils.highlight_code(part_text, 'python')
            want_text = utils.color_text(want_text, 'green')

        if want_lines:
            part_text += '\n' + want_text

        return part_text


if __name__ == '__main__':
    """
    CommandLine:
        python -m xdoctest.doctest_part
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

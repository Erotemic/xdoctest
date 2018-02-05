# -*- coding: utf-8 -*-
"""
Simple storage container used to store a single executable part of a doctest example. Multiple parts are kept by a `xdoctest.doctest_example.Doctest`, which manages execution of each part.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import math
from xdoctest import utils
from xdoctest import checker
from xdoctest import directive
from xdoctest import constants


class DoctestPart(object):
    """
    The result of parsing that represents a "logical block" of code.
    If a want statment is defined, it is stored here.
    """
    def __init__(self, exec_lines, want_lines=None, line_offset=0,
                 orig_lines=None, directives=None):
        self.exec_lines = exec_lines
        self.want_lines = want_lines
        self.line_offset = line_offset
        self.orig_lines = orig_lines
        self.use_eval = False
        self._directives = directives

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
            self._directives = list(directive.extract(self.source))
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

    def check(part, got_stdout, got_eval=constants.NOT_EVALED, runstate=None):
        """
        Check if the "got" output obtained by running this test matches the
        "want" target. Note there are two types of "got" output: (1) output
        from stdout and (2) evaled output. If both are specified, then want may
        match either value.

        Args:
            got_stdout (str): output from stdout
            got_eval (str): output from an eval statement

        Raises:
            GotWantException - If the "got" differs from this parts want.
        """
        return checker.check_got_vs_want(part.want, got_stdout, got_eval,
                                         runstate)

    def format_src(self, linenos=True, want=True, startline=1, n_digits=None,
                   colored=False):
        """
        Customizable formatting of the source and want for this doctest.

        Args:
            linenos (bool): show line numbers
            want (bool): include the want value if it exists
            startline (int): offsets the line numbering
            n_digits (int): number of digits to use for line numbers
            colored (bool): pygmentize the colde

        Example:
            >>> from xdoctest.parser import *
            >>> self = DoctestPart(['print(123)'], ['123'], 0)
            >>> print(self.format_src())
            1 >>> print(123)
              123
        """
        src_text = self.source
        src_text = utils.indent(src_text, '>>> ')
        want_text = self.want if self.want else ''

        if n_digits is None:
            endline = startline + self.n_lines
            n_digits = math.log(max(1, endline), 10)
            n_digits = int(math.ceil(n_digits))

        if linenos:
            src_fmt = '{{:{}d}} {{}}'.format(n_digits)
            want_fmt = '{} {{}}'.format(' ' * n_digits)

            new_lines = []
            count = startline + self.line_offset
            for count, line in enumerate(src_text.splitlines(), start=count):
                new_lines.append(src_fmt.format(count, line))
            if want_text:
                for count, line in enumerate(want_text.splitlines(), start=count):
                    if want:
                        new_lines.append(want_fmt.format(line))
            part_text = '\n'.join(new_lines)
        else:
            if want_text:
                part_text = src_text
                if want:
                    part_text = part_text + '\n' + want_text
            else:
                part_text = src_text
        if colored:
            part_text = utils.highlight_code(part_text, 'python')
        return part_text


if __name__ == '__main__':
    r"""
    CommandLine:
        python -m xdoctest.doctest_part
    """
    import xdoctest
    xdoctest.doctest_module(__file__)

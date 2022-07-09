from _typeshed import Incomplete
from xdoctest import directive

__devnotes__: str


class DoctestPart:
    exec_lines: Incomplete
    want_lines: Incomplete
    line_offset: Incomplete
    orig_lines: Incomplete
    compile_mode: str
    partno: Incomplete

    def __init__(self,
                 exec_lines,
                 want_lines: Incomplete | None = ...,
                 line_offset: int = ...,
                 orig_lines: Incomplete | None = ...,
                 directives: Incomplete | None = ...,
                 partno: Incomplete | None = ...) -> None:
        ...

    @property
    def n_lines(self):
        ...

    @property
    def n_exec_lines(self):
        ...

    @property
    def n_want_lines(self):
        ...

    @property
    def source(self):
        ...

    def compilable_source(self):
        ...

    def has_any_code(self):
        ...

    @property
    def directives(self):
        ...

    @property
    def want(self):
        ...

    def __nice__(self):
        ...

    def check(part,
              got_stdout: str,
              got_eval: str = ...,
              runstate: directive.RuntimeState = None,
              unmatched: list = None) -> None:
        ...

    def format_part(self,
                    linenos: bool = True,
                    want: bool = True,
                    startline: int = 1,
                    n_digits: int = None,
                    colored: bool = False,
                    partnos: bool = False,
                    prefix: bool = True):
        ...

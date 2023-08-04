from typing import List
from xdoctest import directive

__devnotes__: str


class DoctestPart:
    exec_lines: List[str]
    want_lines: List[str] | None
    line_offset: int
    orig_lines: List[str] | None
    partno: int | None
    compile_mode: str

    def __init__(self,
                 exec_lines: List[str],
                 want_lines: List[str] | None = None,
                 line_offset: int = 0,
                 orig_lines: List[str] | None = None,
                 directives: list | None = None,
                 partno: int | None = None) -> None:
        ...

    @property
    def n_lines(self) -> int:
        ...

    @property
    def n_exec_lines(self) -> int:
        ...

    @property
    def n_want_lines(self) -> int:
        ...

    @property
    def source(self) -> str:
        ...

    def compilable_source(self) -> str:
        ...

    def has_any_code(self) -> bool:
        ...

    @property
    def directives(self) -> List[directive.Directive]:
        ...

    @property
    def want(self) -> str | None:
        ...

    def __nice__(self) -> str:
        ...

    def check(part,
              got_stdout: str,
              got_eval: str = ...,
              runstate: directive.RuntimeState | None = None,
              unmatched: list | None = None) -> None:
        ...

    def format_part(self,
                    linenos: bool = True,
                    want: bool = True,
                    startline: int = 1,
                    n_digits: int | None = None,
                    colored: bool = False,
                    partnos: bool = False,
                    prefix: bool = True) -> str:
        ...

from typing import List
from typing import Union
from xdoctest import directive

__devnotes__: str


class DoctestPart:
    exec_lines: List[str]
    want_lines: Union[List[str], None]
    line_offset: int
    orig_lines: Union[List[str], None]
    partno: Union[int, None]
    compile_mode: str

    def __init__(self,
                 exec_lines: List[str],
                 want_lines: Union[List[str], None] = None,
                 line_offset: int = 0,
                 orig_lines: Union[List[str], None] = None,
                 directives: Union[list, None] = None,
                 partno: Union[int, None] = None) -> None:
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
              runstate: Union[directive.RuntimeState, None] = None,
              unmatched: Union[list, None] = None) -> None:
        ...

    def format_part(self,
                    linenos: bool = True,
                    want: bool = True,
                    startline: int = 1,
                    n_digits: Union[int, None] = None,
                    colored: bool = False,
                    partnos: bool = False,
                    prefix: bool = True) -> str:
        ...

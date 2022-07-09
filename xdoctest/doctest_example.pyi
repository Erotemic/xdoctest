from typing import Dict
from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any

__devnotes__: str


class DoctestConfig(dict):

    def __init__(self, *args, **kwargs) -> None:
        ...

    def getvalue(self, key, given: Incomplete | None = ...):
        ...


class DocTest:
    UNKNOWN_MODNAME: str
    UNKNOWN_MODPATH: str
    UNKNOWN_CALLNAME: str
    UNKNOWN_FPATH: str
    block_type: Incomplete
    config: Incomplete
    module: Incomplete
    modpath: Incomplete
    fpath: Incomplete
    modname: Incomplete
    callname: Incomplete
    docsrc: Incomplete
    lineno: Incomplete
    num: Incomplete
    failed_tb_lineno: Incomplete
    exc_info: Incomplete
    failed_part: Incomplete
    warn_list: Incomplete
    logged_evals: Incomplete
    logged_stdout: Incomplete
    global_namespace: Incomplete
    mode: Incomplete

    def __init__(self,
                 docsrc,
                 modpath: Incomplete | None = ...,
                 callname: Incomplete | None = ...,
                 num: int = ...,
                 lineno: int = ...,
                 fpath: Incomplete | None = ...,
                 block_type: Incomplete | None = ...,
                 mode: str = ...) -> None:
        ...

    def __nice__(self):
        ...

    def is_disabled(self, pytest: bool = ...):
        ...

    @property
    def unique_callname(self):
        ...

    @property
    def node(self):
        ...

    @property
    def valid_testnames(self):
        ...

    def wants(self) -> Generator[Any, None, None]:
        ...

    def format_parts(self,
                     linenos: bool = ...,
                     colored: Incomplete | None = ...,
                     want: bool = ...,
                     offset_linenos: Incomplete | None = ...,
                     prefix: bool = ...) -> Generator[Any, None, None]:
        ...

    def format_src(self,
                   linenos: bool = True,
                   colored: bool = None,
                   want: bool = True,
                   offset_linenos: bool = None,
                   prefix: bool = True):
        ...

    def anything_ran(self):
        ...

    def run(self, verbose: int = None, on_error: str = None) -> Dict:
        ...

    @property
    def cmdline(self) -> str:
        ...

    def failed_line_offset(self):
        ...

    def failed_lineno(self):
        ...

    def repr_failure(self, with_tb: bool = ...):
        ...

from typing import Any
from os import PathLike
from types import ModuleType
from types import TracebackType
from typing import Dict
from collections import OrderedDict
from typing import Set
from typing import List
from collections.abc import Generator

from xdoctest.doctest_part import DoctestPart

__devnotes__: str
__docstubs__: str


class DoctestConfig(dict):

    def __init__(self, *args, **kwargs) -> None:
        ...

    def getvalue(self, key: str, given: Any | None = None) -> Any:
        ...


class DocTest:
    UNKNOWN_MODNAME: str
    UNKNOWN_MODPATH: str
    UNKNOWN_CALLNAME: str
    UNKNOWN_FPATH: str
    docsrc: str
    modpath: str | PathLike
    callname: str
    num: int
    lineno: int
    fpath: PathLike
    block_type: str | None
    mode: str
    config: DoctestConfig
    module: ModuleType | None
    modname: str
    failed_tb_lineno: int | None
    exc_info: None | TracebackType
    failed_part: None | DoctestPart
    warn_list: list
    logged_evals: OrderedDict
    logged_stdout: OrderedDict
    global_namespace: dict

    def __init__(self,
                 docsrc: str,
                 modpath: str | PathLike | None = None,
                 callname: str | None = None,
                 num: int = 0,
                 lineno: int = 1,
                 fpath: str | None = None,
                 block_type: str | None = None,
                 mode: str = 'pytest') -> None:
        ...

    def __nice__(self) -> str:
        ...

    def is_disabled(self, pytest: bool = ...) -> bool:
        ...

    @property
    def unique_callname(self) -> str:
        ...

    @property
    def node(self) -> str:
        ...

    @property
    def valid_testnames(self) -> Set[str]:
        ...

    def wants(self) -> Generator[str, None, None]:
        ...

    def format_parts(self,
                     linenos: bool = True,
                     colored: bool | None = None,
                     want: bool = True,
                     offset_linenos: bool | None = None,
                     prefix: bool = True) -> Generator[Any, None, None]:
        ...

    def format_src(self,
                   linenos: bool = True,
                   colored: bool | None = None,
                   want: bool = True,
                   offset_linenos: bool | None = None,
                   prefix: bool = True) -> str:
        ...

    def anything_ran(self) -> bool:
        ...

    def run(self,
            verbose: int | None = None,
            on_error: str | None = None) -> Dict:
        ...

    @property
    def cmdline(self) -> str:
        ...

    def failed_line_offset(self) -> int | None:
        ...

    def failed_lineno(self) -> int | None:
        ...

    def repr_failure(self, with_tb: bool = True) -> List[str]:
        ...

from typing import Any
from typing import Union
from os import PathLike
from typing import Set
from typing import Dict
from typing import List
from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any

__devnotes__: str


class DoctestConfig(dict):

    def __init__(self, *args, **kwargs) -> None:
        ...

    def getvalue(self, key: str, given: Union[Any, None] = None) -> Any:
        ...


class DocTest:
    UNKNOWN_MODNAME: str
    UNKNOWN_MODPATH: str
    UNKNOWN_CALLNAME: str
    UNKNOWN_FPATH: str
    docsrc: str
    modpath: Union[str, PathLike]
    callname: str
    num: int
    lineno: int
    fpath: PathLike
    block_type: Union[str, None]
    mode: str
    config: Incomplete
    module: Incomplete
    modname: Incomplete
    failed_tb_lineno: Incomplete
    exc_info: Incomplete
    failed_part: Incomplete
    warn_list: Incomplete
    logged_evals: Incomplete
    logged_stdout: Incomplete
    global_namespace: Incomplete

    def __init__(self,
                 docsrc: str,
                 modpath: Union[str, PathLike, None] = None,
                 callname: Union[str, None] = None,
                 num: int = 0,
                 lineno: int = 1,
                 fpath: Union[str, None] = None,
                 block_type: Union[str, None] = None,
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
                     colored: Union[bool, None] = None,
                     want: bool = True,
                     offset_linenos: Union[bool, None] = None,
                     prefix: bool = True) -> Generator[Any, None, None]:
        ...

    def format_src(self,
                   linenos: bool = True,
                   colored: Union[bool, None] = None,
                   want: bool = True,
                   offset_linenos: Union[bool, None] = None,
                   prefix: bool = True) -> str:
        ...

    def anything_ran(self) -> bool:
        ...

    def run(self,
            verbose: Union[int, None] = None,
            on_error: Union[str, None] = None) -> Dict:
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

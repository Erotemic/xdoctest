from typing import Union
from typing import List
import xdoctest
import xdoctest.doctest_part
from _typeshed import Incomplete

INDENT_RE: Incomplete
NEED_16806_WORKAROUND: Incomplete
PY2: Incomplete


class DoctestParser:
    simulate_repl: bool

    def __init__(self, simulate_repl: bool = False) -> None:
        ...

    def parse(
        self,
        string: str,
        info: Union[dict,
                    None] = None) -> List[xdoctest.doctest_part.DoctestPart]:
        ...

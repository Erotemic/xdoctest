from typing import Union
from typing import Dict
from collections import OrderedDict
from typing import Any
from typing import List
from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any, NamedTuple
from xdoctest import utils


def named(key, pattern):
    ...


DEFAULT_RUNTIME_STATE: Incomplete


class Effect(NamedTuple):
    action: Incomplete
    key: Incomplete
    value: Incomplete


class RuntimeState(utils.NiceRepr):

    def __init__(self, default_state: Union[None, dict] = None) -> None:
        ...

    def to_dict(self) -> OrderedDict:
        ...

    def __nice__(self) -> str:
        ...

    def __getitem__(self, key: str) -> Any:
        ...

    def __setitem__(self, key: str, value: Any) -> None:
        ...

    def set_report_style(self,
                         reportchoice: str,
                         state: Union[None, Dict] = None) -> None:
        ...

    def update(self, directives: List[Directive]) -> None:
        ...


class Directive(utils.NiceRepr):
    name: str
    args: List[str]
    inline: Union[bool, None]
    positive: bool

    def __init__(self,
                 name: str,
                 positive: bool = True,
                 args: List[str] = ...,
                 inline: Union[bool, None] = None) -> None:
        ...

    @classmethod
    def extract(cls, text: str) -> Generator[Directive, None, None]:
        ...

    def __nice__(self) -> str:
        ...

    def effect(self,
               argv: Incomplete | None = ...,
               environ: Incomplete | None = ...):
        ...

    def effects(self,
                argv: Union[List[str], None] = None,
                environ: Union[Dict[str, str], None] = None) -> List[Effect]:
        ...


COMMANDS: Incomplete
DIRECTIVE_PATTERNS: Incomplete
DIRECTIVE_RE: Incomplete


def parse_directive_optstr(optpart: str,
                           inline: Union[None, bool] = None) -> Directive:
    ...

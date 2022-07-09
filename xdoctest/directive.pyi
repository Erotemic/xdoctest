from typing import List
from typing import Dict
from _typeshed import Incomplete
from collections.abc import Generator
from typing import NamedTuple
from xdoctest import utils


def named(key, pattern):
    ...


DEFAULT_RUNTIME_STATE: Incomplete


class Effect(NamedTuple):
    action: Incomplete
    key: Incomplete
    value: Incomplete


class RuntimeState(utils.NiceRepr):

    def __init__(self, default_state: Incomplete | None = ...) -> None:
        ...

    def to_dict(self):
        ...

    def __nice__(self):
        ...

    def __getitem__(self, key):
        ...

    def __setitem__(self, key, value) -> None:
        ...

    def set_report_style(self,
                         reportchoice,
                         state: Incomplete | None = ...) -> None:
        ...

    def update(self, directives: List[Directive]) -> None:
        ...


class Directive(utils.NiceRepr):
    name: Incomplete
    args: Incomplete
    inline: Incomplete
    positive: Incomplete

    def __init__(self,
                 name,
                 positive: bool = ...,
                 args=...,
                 inline: Incomplete | None = ...) -> None:
        ...

    @classmethod
    def extract(cls, text: str) -> Generator[Directive, None, None]:
        ...

    def __nice__(self):
        ...

    def effect(self,
               argv: Incomplete | None = ...,
               environ: Incomplete | None = ...):
        ...

    def effects(self,
                argv: List[str] = None,
                environ: Dict[str, str] = None) -> List[Effect]:
        ...


COMMANDS: Incomplete
DIRECTIVE_PATTERNS: Incomplete
DIRECTIVE_RE: Incomplete


def parse_directive_optstr(optpart,
                           inline: Incomplete | None = ...) -> Directive:
    ...

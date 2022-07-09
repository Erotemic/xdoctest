from typing import Dict
from typing import List
import ast
from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any
from xdoctest.utils.util_import import is_modname_importable as is_modname_importable, modname_to_modpath as modname_to_modpath, modpath_to_modname as modpath_to_modname, split_modpath as split_modpath

PLAT_IMPL: Incomplete
HAS_UPDATED_LINENOS: Incomplete


class CallDefNode:
    callname: Incomplete
    lineno: Incomplete
    docstr: Incomplete
    doclineno: Incomplete
    doclineno_end: Incomplete
    lineno_end: Incomplete
    args: Incomplete

    def __init__(self,
                 callname,
                 lineno,
                 docstr,
                 doclineno,
                 doclineno_end,
                 args: Incomplete | None = ...) -> None:
        ...


class TopLevelVisitor(ast.NodeVisitor):

    @classmethod
    def parse(cls, source):
        ...

    calldefs: Incomplete
    source: Incomplete
    sourcelines: Incomplete
    assignments: Incomplete

    def __init__(self, source: Incomplete | None = ...) -> None:
        ...

    def syntax_tree(self):
        ...

    def process_finished(self, node) -> None:
        ...

    def visit(self, node) -> None:
        ...

    def visit_FunctionDef(self, node) -> None:
        ...

    def visit_ClassDef(self, node) -> None:
        ...

    def visit_Module(self, node) -> None:
        ...

    def visit_Assign(self, node) -> None:
        ...

    def visit_If(self, node) -> None:
        ...


def parse_static_calldefs(source: str = None,
                          fpath: str = None) -> Dict[str, CallDefNode]:
    ...


def parse_calldefs(source: Incomplete | None = ...,
                   fpath: Incomplete | None = ...):
    ...


def parse_static_value(key: str, source: str = None, fpath: str = None):
    ...


def package_modpaths(pkgpath: str,
                     with_pkg: bool = False,
                     with_mod: bool = True,
                     followlinks: bool = ...,
                     recursive: bool = True,
                     with_libs: bool = False,
                     check: bool = True) -> Generator[str, None, None]:
    ...


def is_balanced_statement(lines: List[str],
                          only_tokens: bool = ...,
                          reraise: int = ...) -> bool:
    ...


def extract_comments(source) -> Generator[Any, None, Any]:
    ...


def six_axt_parse(source_block, filename: str = ..., compatible: bool = ...):
    ...

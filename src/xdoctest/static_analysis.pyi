import ast
from typing import Dict
from collections import OrderedDict
from typing import List
import types
from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any
from xdoctest.utils.util_import import is_modname_importable as is_modname_importable, modname_to_modpath as modname_to_modpath, modpath_to_modname as modpath_to_modname, split_modpath as split_modpath

PLAT_IMPL: Incomplete
HAS_UPDATED_LINENOS: Incomplete


class CallDefNode:
    lineno_end: None | int
    callname: str
    lineno: int
    docstr: str
    doclineno: int
    doclineno_end: int
    args: None | ast.arguments

    def __init__(self,
                 callname: str,
                 lineno: int,
                 docstr: str,
                 doclineno: int,
                 doclineno_end: int,
                 args: None | ast.arguments = None) -> None:
        ...


class TopLevelVisitor(ast.NodeVisitor):
    calldefs: OrderedDict
    source: None | str
    sourcelines: None | List[str]
    assignments: list

    @classmethod
    def parse(cls, source: str):
        ...

    def __init__(self, source: None | str = None) -> None:
        ...

    def syntax_tree(self) -> ast.Module:
        ...

    def process_finished(self, node: ast.AST) -> None:
        ...

    def visit(self, node: ast.AST) -> None:
        ...

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        ...

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        ...

    def visit_Module(self, node: ast.Module) -> None:
        ...

    def visit_Assign(self, node: ast.Assign) -> None:
        ...

    def visit_If(self, node: ast.If) -> None:
        ...


def parse_static_calldefs(source: str | None = None,
                          fpath: str | None = None) -> Dict[str, CallDefNode]:
    ...


def parse_calldefs(source: Incomplete | None = ...,
                   fpath: Incomplete | None = ...):
    ...


def parse_static_value(key: str,
                       source: str | None = None,
                       fpath: str | None = None) -> object:
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


def extract_comments(source: str | List[str]) -> Generator[Any, None, Any]:
    ...


def six_axt_parse(source_block,
                  filename: str = '<source_block>',
                  compatible: bool = True) -> ast.Module | types.CodeType:
    ...

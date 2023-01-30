from typing import Union
import ast
from typing import Dict
from typing import List
import types
import ast
from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any
from xdoctest.utils.util_import import is_modname_importable as is_modname_importable, modname_to_modpath as modname_to_modpath, modpath_to_modname as modpath_to_modname, split_modpath as split_modpath

PLAT_IMPL: Incomplete
HAS_UPDATED_LINENOS: Incomplete


class CallDefNode:
    callname: str
    doclineno: int
    doclineno_end: int
    lineno: Incomplete
    docstr: Incomplete
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
    def parse(cls, source: str):
        ...

    calldefs: Incomplete
    source: Union[None, str]
    sourcelines: Incomplete
    assignments: Incomplete

    def __init__(self, source: Union[None, str] = None) -> None:
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


def parse_static_calldefs(
        source: Union[str, None] = None,
        fpath: Union[str, None] = None) -> Dict[str, CallDefNode]:
    ...


def parse_calldefs(source: Incomplete | None = ...,
                   fpath: Incomplete | None = ...):
    ...


def parse_static_value(key: str,
                       source: Union[str, None] = None,
                       fpath: Union[str, None] = None) -> object:
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


def extract_comments(
        source: Union[str, List[str]]) -> Generator[Any, None, Any]:
    ...


def six_axt_parse(source_block,
                  filename: str = '<source_block>',
                  compatible: bool = True) -> ast.Module | types.CodeType:
    ...

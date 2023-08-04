from os import PathLike
import ast
from _typeshed import Incomplete


class CellDeleter(ast.NodeTransformer):

    def visit(self, node):
        ...


class NotebookLoader:
    default_options: Incomplete
    shell: Incomplete
    path: Incomplete
    options: Incomplete

    def __init__(self, path: Incomplete | None = ...) -> None:
        ...

    def load_module(self,
                    fullname: Incomplete | None = ...,
                    fpath: Incomplete | None = ...):
        ...


def import_notebook_from_path(ipynb_fpath: str | PathLike,
                              only_defs: bool = False):
    ...


def execute_notebook(ipynb_fpath: str | PathLike,
                     timeout: Incomplete | None = ...,
                     verbose: Incomplete | None = ...) -> dict:
    ...

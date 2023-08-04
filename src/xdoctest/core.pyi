from os import PathLike
import xdoctest
from types import ModuleType
from typing import List
from typing import Dict
from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any

import xdoctest.doctest_example

DOCTEST_STYLES: Incomplete
__docstubs__: str


def parse_freeform_docstr_examples(
    docstr: str,
    callname: str | None = None,
    modpath: str | PathLike | None = None,
    lineno: int = 1,
    fpath: str | PathLike | None = None,
    asone: bool = True
) -> Generator[xdoctest.doctest_example.DocTest, None, Any]:
    ...


def parse_google_docstr_examples(
    docstr: str,
    callname: str | None = None,
    modpath: str | PathLike | None = None,
    lineno: int = 1,
    fpath: str | PathLike | None = None,
    eager_parse: bool = True
) -> Generator[xdoctest.doctest_example.DocTest, None, None]:
    ...


def parse_auto_docstr_examples(docstr, *args,
                               **kwargs) -> Generator[Any, None, None]:
    ...


def parse_docstr_examples(
    docstr: str,
    callname: str | None = None,
    modpath: str | PathLike | None = None,
    lineno: int = 1,
    style: str = 'auto',
    fpath: str | PathLike | None = None,
    parser_kw: dict | None = None
) -> Generator[xdoctest.doctest_example.DocTest, None, None]:
    ...


def package_calldefs(pkg_identifier: str | ModuleType,
                     exclude: List[str] = ...,
                     ignore_syntax_errors: bool = True,
                     analysis: str = 'auto') -> Generator[None, None, None]:
    ...


def parse_calldefs(
        module_identifier: str | ModuleType,
        analysis: str = 'auto'
) -> Dict[str, xdoctest.static_analysis.CallDefNode]:
    ...


def parse_doctestables(
    module_identifier: str | PathLike | ModuleType,
    exclude: List[str] = ...,
    style: str = 'auto',
    ignore_syntax_errors: bool = True,
    parser_kw=...,
    analysis: str = 'auto'
) -> Generator[xdoctest.doctest_example.DocTest, None, None]:
    ...

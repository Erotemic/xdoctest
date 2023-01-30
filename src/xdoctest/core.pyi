from typing import Union
from os import PathLike
import xdoctest
from types import ModuleType
from typing import List
from typing import Dict
from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any

DOCTEST_STYLES: Incomplete


def parse_freeform_docstr_examples(
    docstr: str,
    callname: Union[str, None] = None,
    modpath: Union[str, PathLike, None] = None,
    lineno: int = 1,
    fpath: Union[str, PathLike, None] = None,
    asone: bool = True
) -> Generator[xdoctest.doctest_example.DocTest, None, Any]:
    ...


def parse_google_docstr_examples(
    docstr: str,
    callname: Union[str, None] = None,
    modpath: Union[str, PathLike, None] = None,
    lineno: int = 1,
    fpath: Union[str, PathLike, None] = None,
    eager_parse: bool = True
) -> Generator[xdoctest.doctest_example.DocTest, None, None]:
    ...


def parse_auto_docstr_examples(docstr, *args,
                               **kwargs) -> Generator[Any, None, None]:
    ...


def parse_docstr_examples(
    docstr: str,
    callname: Union[str, None] = None,
    modpath: Union[str, PathLike, None] = None,
    lineno: int = 1,
    style: str = 'auto',
    fpath: Union[str, PathLike, None] = None,
    parser_kw: Union[dict, None] = None
) -> Generator[xdoctest.doctest_example.DocTest, None, None]:
    ...


def package_calldefs(pkg_identifier: Union[str, ModuleType],
                     exclude: List[str] = ...,
                     ignore_syntax_errors: bool = True,
                     analysis: str = 'auto') -> Generator[None, None, None]:
    ...


def parse_calldefs(
        module_identifier: Union[str, ModuleType],
        analysis: str = 'auto'
) -> Dict[str, xdoctest.static_analysis.CallDefNode]:
    ...


def parse_doctestables(
    module_identifier: Union[str, PathLike, ModuleType],
    exclude: List[str] = ...,
    style: str = 'auto',
    ignore_syntax_errors: bool = True,
    parser_kw=...,
    analysis: str = 'auto'
) -> Generator[xdoctest.doctest_example.DocTest, None, None]:
    ...

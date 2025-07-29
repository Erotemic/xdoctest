from typing import Any
from typing import List
import xdoctest
from typing import Tuple
from typing import Dict
import pytest
from _pytest._code import code
from _typeshed import Incomplete
from collections.abc import Generator

import xdoctest.doctest_example

__docstubs__: str


def pytest_configure(config: pytest.Config) -> Generator[None, None, None]:
    ...


def pytest_addoption(parser):
    ...


def pytest_collect_file(path, parent):
    ...


class ReprFailXDoctest(code.TerminalRepr):
    reprlocation: Any
    lines: List[str]

    def __init__(self, reprlocation: Any, lines: List[str]) -> None:
        ...

    def toterminal(self, tw) -> None:
        ...


class XDoctestItem(pytest.Item):
    cls: Incomplete
    example: xdoctest.doctest_example.DocTest
    obj: Incomplete
    fixture_request: Incomplete

    def __init__(
            self,
            name: str,
            parent: Any | None,
            example: xdoctest.doctest_example.DocTest | None = None) -> None:
        ...

    def setup(self) -> None:
        ...

    def runtest(self) -> None:
        ...

    def repr_failure(self, excinfo):
        ...

    def reportinfo(self) -> Tuple[str, int, str]:
        ...


class _XDoctestBase(pytest.Module):
    ...


class XDoctestTextfile(_XDoctestBase):
    obj: Incomplete

    def collect(self) -> Generator[XDoctestItem, None, None]:
        ...


class XDoctestModule(_XDoctestBase):

    def collect(self) -> Generator[Any, None, None]:
        ...


def xdoctest_namespace() -> Dict:
    ...

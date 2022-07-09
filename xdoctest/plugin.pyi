import pytest
from _pytest._code import code
from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any


def monkey_patch_disable_normal_doctest():
    ...


def pytest_addoption(parser):
    ...


def pytest_collect_file(path, parent):
    ...


class ReprFailXDoctest(code.TerminalRepr):
    reprlocation: Incomplete
    lines: Incomplete

    def __init__(self, reprlocation, lines) -> None:
        ...

    def toterminal(self, tw) -> None:
        ...


class XDoctestItem(pytest.Item):
    cls: Incomplete
    example: Incomplete
    obj: Incomplete
    fixture_request: Incomplete

    def __init__(self, name, parent, example: Incomplete | None = ...) -> None:
        ...

    def setup(self) -> None:
        ...

    def runtest(self) -> None:
        ...

    def repr_failure(self, excinfo):
        ...

    def reportinfo(self):
        ...


class _XDoctestBase(pytest.Module):
    ...


class XDoctestTextfile(_XDoctestBase):
    obj: Incomplete

    def collect(self) -> Generator[Any, None, None]:
        ...


class XDoctestModule(_XDoctestBase):

    def collect(self) -> Generator[Any, None, None]:
        ...


def xdoctest_namespace():
    ...

from typing import Union
import xdoctest
from typing import Tuple
from _typeshed import Incomplete

unicode_literal_re: Incomplete
bytes_literal_re: Incomplete
BLANKLINE_MARKER: str
ELLIPSIS_MARKER: str
TRAILING_WS: Incomplete


def check_got_vs_want(want: str,
                      got_stdout: str,
                      got_eval: str = ...,
                      runstate: Union[xdoctest.directive.RuntimeState,
                                      None] = None):
    ...


def extract_exc_want(want: str) -> str:
    ...


def check_exception(
        exc_got: str,
        want: str,
        runstate: Union[xdoctest.directive.RuntimeState, None] = None) -> bool:
    ...


def check_output(
        got: str,
        want: str,
        runstate: Union[xdoctest.directive.RuntimeState, None] = None) -> bool:
    ...


def normalize(
    got: str,
    want: str,
    runstate: Union[xdoctest.directive.RuntimeState, None] = None
) -> Tuple[str, str]:
    ...


class ExtractGotReprException(AssertionError):
    orig_ex: Exception

    def __init__(self, msg: str, orig_ex: Exception) -> None:
        ...


class GotWantException(AssertionError):
    got: str
    want: str

    def __init__(self, msg: str, got: str, want: str) -> None:
        ...

    def output_difference(self,
                          runstate: Union[xdoctest.directive.RuntimeState,
                                          None] = None,
                          colored: bool = True) -> str:
        ...

    def output_repr_difference(
            self,
            runstate: Union[xdoctest.directive.RuntimeState,
                            None] = None) -> str:
        ...


def remove_blankline_marker(text: str) -> str:
    ...

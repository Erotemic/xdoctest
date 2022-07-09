from _typeshed import Incomplete

unicode_literal_re: Incomplete
bytes_literal_re: Incomplete
BLANKLINE_MARKER: str
ELLIPSIS_MARKER: str
TRAILING_WS: Incomplete


def check_got_vs_want(want: str,
                      got_stdout: str,
                      got_eval: str = ...,
                      runstate: Incomplete | None = ...):
    ...


def extract_exc_want(want):
    ...


def check_exception(exc_got, want, runstate: Incomplete | None = ...):
    ...


def check_output(got, want, runstate: Incomplete | None = ...):
    ...


def normalize(got, want, runstate: Incomplete | None = ...):
    ...


class ExtractGotReprException(AssertionError):
    orig_ex: Incomplete

    def __init__(self, msg, orig_ex) -> None:
        ...


class GotWantException(AssertionError):
    got: Incomplete
    want: Incomplete

    def __init__(self, msg, got, want) -> None:
        ...

    def output_difference(self,
                          runstate: Incomplete | None = ...,
                          colored: bool = ...):
        ...

    def output_repr_difference(self, runstate: Incomplete | None = ...):
        ...


def remove_blankline_marker(text):
    ...

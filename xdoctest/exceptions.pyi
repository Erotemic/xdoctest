from _typeshed import Incomplete


class MalformedDocstr(Exception):
    ...


class DoctestParseError(Exception):
    msg: Incomplete
    string: Incomplete
    info: Incomplete
    orig_ex: Incomplete

    def __init__(self,
                 msg,
                 string: Incomplete | None = ...,
                 info: Incomplete | None = ...,
                 orig_ex: Incomplete | None = ...) -> None:
        ...


class ExitTestException(Exception):
    ...


class IncompleteParseError(SyntaxError):
    ...


class _pytest:

    class outcomes:

        class Skipped(Exception):
            ...

from typing import Any
from typing import Any


class MalformedDocstr(Exception):
    ...


class DoctestParseError(Exception):
    msg: str
    string: str
    info: Any
    orig_ex: Exception

    def __init__(self,
                 msg: str,
                 string: str = None,
                 info: Any = None,
                 orig_ex: Exception = None) -> None:
        ...


class ExitTestException(Exception):
    ...


class IncompleteParseError(SyntaxError):
    ...


class _pytest:

    class outcomes:

        class Skipped(Exception):
            ...

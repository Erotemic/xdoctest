from typing import Union
from typing import Any
from typing import Any


class MalformedDocstr(Exception):
    ...


class DoctestParseError(Exception):
    msg: str
    string: Union[str, None]
    info: Union[Any, None]
    orig_ex: Union[Exception, None]

    def __init__(self,
                 msg: str,
                 string: Union[str, None] = None,
                 info: Union[Any, None] = None,
                 orig_ex: Union[Exception, None] = None) -> None:
        ...


class ExitTestException(Exception):
    ...


class IncompleteParseError(SyntaxError):
    ...


class _pytest:

    class outcomes:

        class Skipped(Exception):
            ...

from typing import Callable
from types import ModuleType
from typing import List
from typing import Dict
from typing import Any
from typing import Set
from _typeshed import Incomplete


def log(msg: str, verbose: int, level: int = 1) -> None:
    ...


def doctest_callable(func: Callable) -> None:
    ...


def gather_doctests(doctest_identifiers,
                    style: str = ...,
                    analysis: str = ...,
                    verbose: Incomplete | None = ...) -> None:
    ...


def doctest_module(module_identifier: str | ModuleType | None = None,
                   command: str | None = None,
                   argv: List[str] | None = None,
                   exclude: List[str] = ...,
                   style: str = 'auto',
                   verbose: int | None = None,
                   config: Dict[str, object] | None = None,
                   durations: int | None = None,
                   analysis: str = 'auto') -> Dict[str, Any]:
    ...


def undefined_names(sourcecode: str) -> Set[str]:
    ...

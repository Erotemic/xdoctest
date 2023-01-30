from typing import Callable
from typing import Union
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


def doctest_module(module_identifier: Union[str, ModuleType, None] = None,
                   command: Union[str, None] = None,
                   argv: Union[List[str], None] = None,
                   exclude: List[str] = ...,
                   style: str = 'auto',
                   verbose: Union[int, None] = None,
                   config: Union[Dict[str, object], None] = None,
                   durations: Union[int, None] = None,
                   analysis: str = 'auto') -> Dict[str, Any]:
    ...


def undefined_names(sourcecode: str) -> Set[str]:
    ...

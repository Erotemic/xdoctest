from typing import Callable
from typing import Union
from types import ModuleType
from typing import List
from typing import Dict
from typing import Any


def log(msg: str, verbose: int) -> None:
    ...


def doctest_callable(func: Callable) -> None:
    ...


def doctest_module(module_identifier: Union[str, ModuleType, None] = None,
                   command: str = None,
                   argv: Union[List[str], None] = None,
                   exclude: List[str] = ...,
                   style: str = ...,
                   verbose: Union[int, None] = None,
                   config: Dict[str, object] = None,
                   durations: Union[int, None] = None,
                   analysis: str = 'auto') -> Dict[str, Any]:
    ...

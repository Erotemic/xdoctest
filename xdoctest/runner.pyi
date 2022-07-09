from typing import Callable
from typing import Union
from types import ModuleType
from typing import List
from typing import Dict


def log(msg, verbose) -> None:
    ...


def doctest_callable(func: Callable) -> None:
    ...


def doctest_module(module_identifier: Union[str, ModuleType, None] = None,
                   command: str = None,
                   argv: List[str] = None,
                   exclude: List[str] = ...,
                   style: str = ...,
                   verbose: int = None,
                   config: Dict[str, object] = None,
                   durations: int = None,
                   analysis: str = 'auto') -> Dict:
    ...

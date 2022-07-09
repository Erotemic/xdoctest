from typing import Union
from os import PathLike
from types import ModuleType
from typing import Dict
import xdoctest
from types import FrameType
from typing import Callable
from typing import Tuple
from collections.abc import Generator
from typing import Any


def parse_dynamic_calldefs(
    modpath_or_module: Union[str, PathLike, ModuleType]
) -> Dict[str, xdoctest.static_analysis.CallDefNode]:
    ...


def get_stack_frame(n: int = 0, strict: bool = True) -> FrameType:
    ...


def get_parent_frame(n: int = 0) -> FrameType:
    ...


def iter_module_doctestables(
        module: ModuleType) -> Generator[Tuple[str, Callable], None, Any]:
    ...


def is_defined_by_module(item: object, module: ModuleType):
    ...

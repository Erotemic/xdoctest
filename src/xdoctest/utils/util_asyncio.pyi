import sys
from typing import Any, TypeVar, final
if sys.version_info >= (3, 9):
    from collections.abc import Coroutine
else:
    from typing import Coroutine

_T = TypeVar('_T')

@final
class FallbackRunner:
    def __init__(self) -> None: ...
    def run(self, coro: Coroutine[Any, Any, _T]) -> _T: ...
    def close(self) -> None: ...

def running() -> bool: ...

if sys.version_info >= (3, 11):
    from asyncio import Runner
else:
    Runner = FallbackRunner

from _typeshed import Incomplete


class TempDir:
    dpath: Incomplete
    persist: Incomplete

    def __init__(self, persist: bool = ...) -> None:
        ...

    def __del__(self) -> None:
        ...

    def ensure(self):
        ...

    def cleanup(self) -> None:
        ...

    def __enter__(self):
        ...

    def __exit__(self, type_, value, trace) -> None:
        ...


def ensuredir(dpath: str, mode: int = 1023) -> str:
    ...

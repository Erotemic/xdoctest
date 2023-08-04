import io
from _typeshed import Incomplete


class TeeStringIO(io.StringIO):
    redirect: io.IOBase
    buffer: Incomplete

    def __init__(self, redirect: Incomplete | None = ...) -> None:
        ...

    def isatty(self):
        ...

    def fileno(self):
        ...

    @property
    def encoding(self):
        ...

    def write(self, msg):
        ...

    def flush(self):
        ...


class CaptureStream:
    ...


class CaptureStdout(CaptureStream):
    enabled: Incomplete
    suppress: Incomplete
    orig_stdout: Incomplete
    cap_stdout: Incomplete
    text: Incomplete
    parts: Incomplete
    started: bool

    def __init__(self,
                 suppress: bool = ...,
                 enabled: bool = ...,
                 **kwargs) -> None:
        ...

    def log_part(self) -> None:
        ...

    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...

    def __enter__(self):
        ...

    def __del__(self) -> None:
        ...

    def close(self) -> None:
        ...

    def __exit__(self, type_, value, trace):
        ...

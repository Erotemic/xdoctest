from _typeshed import Incomplete


def myfunc():
    ...


class MyClass:
    data: Incomplete

    def __init__(self, *args, **kw) -> None:
        ...

    @classmethod
    def demo(cls, **kw):
        ...

    @staticmethod
    def always_fails() -> None:
        ...

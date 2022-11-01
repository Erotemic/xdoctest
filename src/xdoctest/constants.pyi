from _typeshed import Incomplete


class _NOT_EVAL_TYPE:

    def __new__(cls):
        ...

    def __reduce__(self):
        ...

    def __copy__(self):
        ...

    def __deepcopy__(self, memo):
        ...

    def __call__(self, default) -> None:
        ...

    def __bool__(self):
        ...

    __nonzero__: Incomplete


NOT_EVALED: _NOT_EVAL_TYPE

from _typeshed import Incomplete

NO_COLOR: Incomplete


def strip_ansi(text):
    ...


def color_text(text: str, color: str) -> str:
    ...


def ensure_unicode(text):
    ...


def indent(text: str, prefix: str = '    ') -> str:
    ...


def highlight_code(text: str, lexer_name: str = 'python', **kwargs) -> str:
    ...


def add_line_numbers(source,
                     start: int = ...,
                     n_digits: Incomplete | None = ...):
    ...


def codeblock(block_str: str) -> str:
    ...

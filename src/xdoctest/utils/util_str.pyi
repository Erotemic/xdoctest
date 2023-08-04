from typing import List
from _typeshed import Incomplete

NO_COLOR: Incomplete


def strip_ansi(text: str) -> str:
    ...


def color_text(text: str, color: str) -> str:
    ...


def ensure_unicode(text: str) -> str:
    ...


def indent(text: str, prefix: str = '    ') -> str:
    ...


def highlight_code(text: str, lexer_name: str = 'python', **kwargs) -> str:
    ...


def add_line_numbers(source: str | List[str],
                     start: int = 1,
                     n_digits: int | None = None) -> List[str] | str:
    ...


def codeblock(block_str: str) -> str:
    ...

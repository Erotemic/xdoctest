from typing import List
from typing import Tuple
from typing import Dict
from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any, NamedTuple


class DocBlock(NamedTuple):
    text: Incomplete
    offset: Incomplete


def split_google_docblocks(docstr: str) -> List[Tuple[str, DocBlock]]:
    ...


def parse_google_args(docstr: str) -> Generator[Dict[str, str], None, None]:
    ...


def parse_google_returns(
        docstr: str,
        return_annot: str | None = None
) -> Generator[Dict[str, str], None, None]:
    ...


def parse_google_retblock(
        lines: str,
        return_annot: str | None = None
) -> Generator[Dict[str, str], None, Any]:
    ...


def parse_google_argblock(
        lines: str,
        clean_desc: bool = True
) -> Generator[Dict[str, str | None], None, Any]:
    ...

"""Regression tests for Google-style argument parsing."""

from time import perf_counter

from xdoctest.docstr.docscrape_google import parse_google_argblock


def test_google_argblock_type_spacing() -> None:
    lines = '\n'.join(
        [
            'alpha  ( int )  : a description',
            'beta (Dict[str, str]): another description',
            '*args : positional values',
            'gamma (  ): empty type',
        ]
    )
    parsed = list(parse_google_argblock(lines))
    assert [(p['name'], p['type'], p['desc']) for p in parsed] == [
        ('alpha', 'int', 'a description'),
        ('beta', 'Dict[str, str]', 'another description'),
        ('*args', None, 'positional values'),
        ('gamma', '', 'empty type'),
    ]


def test_google_argblock_malformed_whitespace_is_fast() -> None:
    # A name with no colon and an unclosed type used to trigger quadratic
    # and worse backtracking, respectively. These sizes separate those
    # regressions from normal regex overhead with ample CI headroom.
    for malformed in ('arg' + ' ' * 80_000, 'arg (' + ' ' * 2_500):
        start = perf_counter()
        assert list(parse_google_argblock(malformed)) == []
        assert perf_counter() - start < 2.0

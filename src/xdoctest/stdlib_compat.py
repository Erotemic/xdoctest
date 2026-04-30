"""
Generic intake seam: convert stdlib-doctest-shaped objects into runnable
:class:`xdoctest.doctest_example.DocTest` instances.

This module is the third-party adapter surface for tools that already produce
stdlib :class:`doctest.Example` lists (:mod:`pytest_doctestplus`, sphinx
extensions, custom collectors) and want xdoctest's runner without writing
their own runner adapter.

The intake function :func:`from_examples` is intentionally generic — it does
not import or know about any specific tool. It accepts any sequence of
example-like objects with the standard ``source``, ``want``, ``lineno``,
``options`` shape.

Line numbers are preserved by reconstructing a ``>>>``-prefixed doctest source
string with blank-line padding so that the first example's line in the
synthesized source matches its original ``lineno`` offset, and the
``DocTest.lineno`` is set to that base. xdoctest's parser then assigns each
part a ``line_offset`` such that
``dtest.lineno + part.line_offset == original_file_line``.

Where additional precision is desired (e.g. multi-line PS1/PS2 statements
that would otherwise collapse to start-of-Example), xdoctest's parser is
already statement-aware once it parses the reconstructed source — no extra
work needed.
"""

from __future__ import annotations

import doctest as _doctest
from typing import Any, Iterable, Mapping, Optional

from xdoctest import directive_facade
from xdoctest.doctest_example import DocTest


def from_examples(
    examples: Iterable[Any],
    *,
    globs: Optional[Mapping[str, Any]] = None,
    name: str = '<doctest>',
    filename: Optional[str] = None,
    lineno: Optional[int] = None,
    optionflags: int = 0,
    config: Optional[Mapping[str, Any]] = None,
) -> DocTest:
    """
    Build a runnable xdoctest :class:`DocTest` from a sequence of stdlib-like
    example objects.

    Args:
        examples: iterable of objects each with ``source``, ``want``,
            ``lineno`` and (optionally) ``options`` attributes — i.e. the
            stdlib :class:`doctest.Example` shape.
        globs: namespace dict for the doctest. Mirrors stdlib
            ``DocTest.globs``. Defaults to ``{'__name__': '__main__'}``.
        name: human-readable test name; mirrors stdlib ``DocTest.name``.
        filename: source file path; mirrors stdlib ``DocTest.filename``.
            Used by xdoctest for failure reporting.
        lineno: explicit base line number. If ``None``, the first example's
            ``lineno`` is used so that ``dtest.lineno + part.line_offset``
            recovers absolute file line numbers.
        optionflags: stdlib-doctest optionflags ``int``. Bits that map to
            xdoctest builtin flags are translated into runtime state defaults;
            the rest are kept as checker-only optionflag bits and delivered
            to the active output checker.
        config: optional mapping of doctestplus-style :class:`DoctestConfig`
            keys to merge into the resulting ``DocTest.config``. Most useful
            for setting ``output_checker`` to select a registered checker.

    Returns:
        DocTest: configured to run via :meth:`DocTest.run`.

    Notes:
        Examples whose ``options[doctest.SKIP]`` is ``True`` are encoded as
        an inline ``# xdoctest: +SKIP`` directive on the example's first
        source line. Other registered checker-only flags work analogously
        when explicitly passed via ``optionflags``.
    """
    examples = list(examples)
    if globs is None:
        globs = {'__name__': '__main__'}

    base, docsrc, _ = _build_docsrc(examples)
    if lineno is None:
        lineno = base if base is not None else 0

    # Pass filename as ``fpath`` (display path) rather than ``modpath`` so we
    # don't force a stdlib-style modname lookup against the filesystem; the
    # input may be a ``.rst`` file or a synthetic name that doesn't resolve
    # to a Python module.
    dtest = DocTest(
        docsrc=docsrc,
        modpath=None,
        callname=name,
        num=0,
        lineno=lineno,
        fpath=filename,
    )
    dtest.global_namespace = dict(globs)

    # Configure checker selection / persistent checker flags.
    if config:
        for key, value in config.items():
            dtest.config[key] = value
    if optionflags:
        # Persistent checker-only optionflag bits flow through
        # output_checker_flags. Builtin xdoctest flags (ELLIPSIS,
        # NORMALIZE_WHITESPACE, etc.) are converted into the structured
        # default_runtime_state via optionflags_to_runtime_state.
        runstate = directive_facade.optionflags_to_runtime_state(optionflags)
        defaults: dict = dict(dtest.config.get('default_runtime_state') or {})
        for key, value in runstate.to_dict().items():
            if isinstance(value, bool):
                defaults[key] = value
        dtest.config['default_runtime_state'] = defaults
        dtest.config['output_checker_flags'] = int(optionflags)

    return dtest


def from_stdlib_doctest(
    stdlib_test: _doctest.DocTest,
    *,
    optionflags: int = 0,
    config: Optional[Mapping[str, Any]] = None,
) -> DocTest:
    """
    Convenience: convert a stdlib :class:`doctest.DocTest` directly. The
    metadata (``name``, ``filename``, ``lineno``, ``globs``) is taken from
    the input.
    """
    # In stdlib, ``DocTest.lineno`` is the line of the docstring in the file
    # and each ``Example.lineno`` is an offset within that docstring. So the
    # absolute file line of the first example is ``stdlib_test.lineno +
    # examples[0].lineno``. We pass that sum as the converter base so xdoctest
    # reports ``dtest.lineno + part.line_offset`` as absolute file line.
    examples = list(stdlib_test.examples)
    if examples:
        absolute_base = (stdlib_test.lineno or 0) + (examples[0].lineno or 0)
    else:
        absolute_base = stdlib_test.lineno or 0
    return from_examples(
        examples,
        globs=stdlib_test.globs,
        name=stdlib_test.name,
        filename=stdlib_test.filename,
        lineno=absolute_base,
        optionflags=optionflags,
        config=config,
    )


def _build_docsrc(examples):
    """
    Reconstruct a ``>>>``-prefixed doctest source string from stdlib-shaped
    examples, padding with blank lines so each example's prompt line in the
    reconstructed source mirrors its original ``Example.lineno`` offset.

    Returns ``(base_lineno, docsrc, line_map)`` where:

    - ``base_lineno`` is the lineno of the first example (the offset that
      should be passed to :class:`DocTest.lineno` so absolute file lines can
      be recovered), or ``None`` if no examples were provided.
    - ``docsrc`` is the reconstructed source.
    - ``line_map`` maps each rebuilt-source line index to the original
      example index it came from (for diagnostics).
    """
    if not examples:
        return None, '', {}

    base = examples[0].lineno
    lines: list[str] = []
    line_map: dict[int, Optional[int]] = {}
    cursor = 0

    for idx, ex in enumerate(examples):
        target = (ex.lineno or 0) - base
        # Pad blank lines so the prompt aligns with the original lineno.
        while cursor < target:
            line_map[cursor] = None
            lines.append('')
            cursor += 1

        is_skip = bool((getattr(ex, 'options', None) or {}).get(_doctest.SKIP))

        src_lines = (ex.source or '').splitlines() or ['']
        for i, line in enumerate(src_lines):
            prefix = '>>> ' if i == 0 else '... '
            text = prefix + line
            if i == 0 and is_skip:
                text = text.rstrip() + '  # xdoctest: +SKIP'
            line_map[cursor] = idx
            lines.append(text)
            cursor += 1

        if ex.want:
            for w in ex.want.splitlines():
                line_map[cursor] = idx
                lines.append(w)
                cursor += 1

    return base, '\n'.join(lines), line_map


__all__ = [
    'from_examples',
    'from_stdlib_doctest',
]

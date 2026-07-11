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

Fidelity guarantees:

- **Line numbers**: the reconstructed docsrc pads with blank lines so that
  each example's prompt line matches its original ``lineno`` offset, and
  ``DocTest.lineno`` is set to the first example's base line. xdoctest's
  parser then assigns each part a ``line_offset`` such that
  ``dtest.lineno + part.line_offset == original_file_line``.
- **Source content**: example source is carried verbatim (only the standard
  ``>>> `` / ``... `` prompts are re-added). Per-example semantics from
  ``Example.options`` are attached to the parsed parts as *structured*
  :class:`~xdoctest.directive.Directive` objects — never by injecting
  directive comments into the source text.

Option semantics flow through one channel: each named stdlib optionflag in
``Example.options`` becomes a per-part directive. Flags whose names match
xdoctest runtime-state keys (``SKIP``, ``ELLIPSIS``, ``IGNORE_WARNINGS``,
...) modify the structured runtime state; any other *named* flag is adopted
as a checker-only optionflag and delivered to the active output checker via
the standard ``flags`` argument. Since consecutive want-less examples merge
into a single xdoctest part, per-example options apply at part granularity.
"""

from __future__ import annotations

import bisect
import doctest as _doctest
from typing import Any, Iterable, Mapping, Optional

from xdoctest import directive, directive_facade
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
        optionflags: stdlib-doctest optionflags ``int`` applying to the whole
            test. Bits that map to xdoctest builtin flags are translated into
            runtime state defaults; the rest are kept as checker-only
            optionflag bits and delivered to the active output checker.
        config: optional mapping of :class:`DoctestConfig` keys to merge into
            the resulting ``DocTest.config``. Most useful for setting
            ``output_checker`` to select a registered checker.

    Returns:
        DocTest: configured to run via :meth:`DocTest.run`.

    Notes:
        Per-example ``options`` are attached as structured per-part
        directives (see module docstring); the source text is never
        rewritten.
    """
    examples = list(examples)
    if globs is None:
        globs = {'__name__': '__main__'}

    base, docsrc, example_starts = _build_docsrc(examples)
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

    _attach_option_directives(dtest, examples, example_starts)
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

    Returns ``(base_lineno, docsrc, example_starts)`` where:

    - ``base_lineno`` is the lineno of the first example (the offset that
      should be passed to :class:`DocTest.lineno` so absolute file lines can
      be recovered), or ``None`` if no examples were provided.
    - ``docsrc`` is the reconstructed source.
    - ``example_starts`` is a list of ``(docsrc_line, example_index)`` pairs
      recording where each example's source begins in the rebuilt docsrc.
    """
    if not examples:
        return None, '', []

    base = examples[0].lineno
    lines: list[str] = []
    example_starts: list[tuple[int, int]] = []
    cursor = 0

    for idx, ex in enumerate(examples):
        target = (ex.lineno or 0) - base
        # Pad blank lines so the prompt aligns with the original lineno.
        while cursor < target:
            lines.append('')
            cursor += 1

        example_starts.append((cursor, idx))
        src_lines = (ex.source or '').splitlines() or ['']
        for i, line in enumerate(src_lines):
            prefix = '>>> ' if i == 0 else '... '
            lines.append(prefix + line)
            cursor += 1

        if ex.want:
            for w in ex.want.splitlines():
                lines.append(w)
                cursor += 1

    return base, '\n'.join(lines), example_starts


def _attach_option_directives(dtest, examples, example_starts):
    """
    Translate per-example ``options`` dicts into structured per-part
    directives on the parsed :class:`DocTest`.

    xdoctest may merge consecutive want-less examples into one part, so each
    part collects the options of every example whose source starts within
    its line span (later examples win on conflicting flags).
    """
    if not example_starts:
        return
    if not any(getattr(examples[idx], 'options', None) for _, idx in example_starts):
        return

    dtest._parse()
    parts = dtest._parts or []
    if not parts:
        return

    part_offsets = [part.line_offset for part in parts]
    examples_by_part: dict[int, list[int]] = {}
    for start_line, ex_idx in example_starts:
        partx = bisect.bisect_right(part_offsets, start_line) - 1
        if partx < 0:
            continue
        examples_by_part.setdefault(partx, []).append(ex_idx)

    for partx, ex_idxs in examples_by_part.items():
        merged: dict = {}
        for ex_idx in ex_idxs:
            merged.update(getattr(examples[ex_idx], 'options', None) or {})
        extra = _options_to_directives(merged)
        if extra:
            part = parts[partx]
            # Preserve directives written inline in the original source;
            # structured options come after so they win on conflict.
            part._directives = list(part.directives) + extra


def _options_to_directives(options):
    """
    Convert a stdlib-style ``{flag_bit: bool}`` options dict into a list of
    per-part (inline) :class:`~xdoctest.directive.Directive` objects.

    Unnamed bits are silently dropped (they cannot be expressed); named bits
    unknown to xdoctest are adopted as checker-only optionflags.
    """
    if not options:
        return []
    names_by_bit = {
        bit: name for name, bit in _doctest.OPTIONFLAGS_BY_NAME.items()
    }
    directives = []
    for flag, value in options.items():
        name = names_by_bit.get(flag)
        if name is None:
            continue
        name = name.upper()
        if (
            name not in directive.COMMANDS
            and not directive_facade.is_registered_optionflag(name)
        ):
            # Adopt any stdlib-registered flag so the directive system can
            # carry it through to the output checker as a checker-only bit.
            directive_facade.register_optionflag(name)
        directives.append(
            directive.Directive(name, positive=bool(value), inline=True)
        )
    return directives


__all__ = [
    'from_examples',
    'from_stdlib_doctest',
]

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
the standard ``flags`` argument. Each incoming stdlib example is parsed as
its own execution boundary, so its options never leak to adjacent examples.
"""

from __future__ import annotations

import doctest as _doctest
from typing import Any, Iterable, Mapping, Optional

from xdoctest import directive, directive_facade, parser
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

    base, docsrc = _build_docsrc(examples)
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

    _parse_examples_as_parts(dtest, examples, base)
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

    Returns ``(base_lineno, docsrc)`` where ``base_lineno`` is the lineno
    of the first example (or ``None`` for an empty input), and ``docsrc``
    is the reconstructed source.
    """
    if not examples:
        return None, ''

    base = examples[0].lineno
    lines: list[str] = []
    cursor = 0

    for ex in examples:
        target = (ex.lineno or 0) - base
        # Pad blank lines so the prompt aligns with the original lineno.
        while cursor < target:
            lines.append('')
            cursor += 1

        example_lines = _example_docsrc_lines(ex)
        lines.extend(example_lines)
        cursor += len(example_lines)

    return base, '\n'.join(lines)


def _parse_examples_as_parts(dtest, examples, base):
    """Parse each stdlib example independently and concatenate its parts.

    A stdlib :class:`doctest.Example` is an execution and option-scope
    boundary. Parsing the reconstructed full docsrc in one pass can merge
    adjacent want-less examples into one xdoctest part, which broadens options
    such as ``SKIP`` to statements that belong to a different example. Parse
    each incoming example independently so its options apply only to the code
    it owns, while retaining the reconstructed full docsrc for display.
    """
    if not examples:
        return

    base = 0 if base is None else base
    parts = []
    for ex in examples:
        local_docsrc = '\n'.join(_example_docsrc_lines(ex))
        info = {
            'callname': dtest.callname,
            'modpath': dtest.modpath,
            'lineno': dtest.lineno,
            'fpath': dtest.fpath,
        }
        raw_parts = parser.DoctestParser().parse(local_docsrc, info)
        local_parts = [part for part in raw_parts if not isinstance(part, str)]
        line_offset = (ex.lineno or 0) - base
        for part in local_parts:
            part.line_offset += line_offset
            extra = _options_to_directives(getattr(ex, 'options', None) or {})
            if extra:
                # Preserve directives written inline in the original source;
                # structured stdlib options come after so they win on conflict.
                part._directives = list(part.directives) + extra
            parts.append(part)
    dtest._parts = parts


def _example_docsrc_lines(ex):
    """Reconstruct the prompted source and want lines for one example."""
    lines = []
    src_lines = (ex.source or '').splitlines() or ['']
    for idx, line in enumerate(src_lines):
        prefix = '>>> ' if idx == 0 else '... '
        lines.append(prefix + line)
    if ex.want:
        lines.extend(ex.want.splitlines())
    return lines



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

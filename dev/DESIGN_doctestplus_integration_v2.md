# doctestplus ↔ xdoctest integration — refined design (v2)

Status: design proposal, 2026-07-02.
Supersedes the staged GPT-5.5 plan; grounded in what is actually on
`dev/doctestplus-compat` (xdoctest) and `dev/xdoctest-compat`
(tpl/pytest-doctestplus) as of commits `947419c` / `f409a0b`.

## 1. Verdict on the current implementation

The end-to-end pipeline works: `pytest --doctest-plus
--doctest-plus-backend=xdoctest` runs doctestplus-collected doctests through
xdoctest's runner, and the reverse (`--xdoctest` + doctestplus checker) works
too. The one-way dependency rule is respected. But the implementation has
grown **three parallel channels for the same per-example semantics**, and the
doctestplus "backend-neutral object" layer carries almost no information:

1. **RuntimeState directives** (structured, xdoctest-native).
2. **Checker-only optionflag bits** (`output_checker_flags` int).
3. **Warning-policy side channel**: neutral `warning_policy` field →
   `warning_policy` callback param on `from_examples` →
   `_detect_warning_policy_from_options` name-sniffing fallback →
   `_WarningAwareDocTest` subclass + `_stdlib_compat_line_map` stash.

All three encode "what should be true while this example runs." The elegant
design collapses them into **one**.

## 2. The organizing principle

> **`Example.options` (stdlib flag bits) is the wire format.
> The optionflag registry is the codec.
> `RuntimeState` is the internal truth.**

- Anything a third party wants to say about an example is said in the stdlib
  vocabulary: a flag bit in `Example.options`, registered by name via
  `xdoctest.register_optionflag(name, runtime_state_key=None)`.
- The registry (already built: `directive_facade.RuntimeFlagFacade`) is the
  single translation layer. Flags bound to a runtime key become structured
  state; unbound flags ride as checker-only bits.
- Inside xdoctest nothing but `RuntimeState` is consulted — including for
  warnings policy.

Consequence: `from_examples` needs **no** semantic special cases. Not for
SKIP, not for warnings, not for future flags. It maps `options` dicts through
the codec, generically.

## 3. xdoctest changes

### 3.1 Warning policy becomes a native directive (new feature, not compat glue)

Add `IGNORE_WARNINGS: bool` and `SHOW_WARNINGS: bool` to
`DEFAULT_RUNTIME_STATE`. The runner (the existing `_part_context` seam, now a
concrete private implementation rather than an override point) consults the
runstate after per-part directives are applied:

- `IGNORE_WARNINGS` → `warnings.catch_warnings()` + `simplefilter('ignore')`
  around part exec.
- `SHOW_WARNINGS` → record + print `Category: message` lines inside the
  capture, so they participate in got/want matching (doctestplus-compatible
  surface).

This gives every xdoctest user `# xdoctest: +IGNORE_WARNINGS` /
`+SHOW_WARNINGS` — a real standalone improvement — and doctestplus gets it for
free by registering its flags with
`register_optionflag('IGNORE_WARNINGS', runtime_state_key='IGNORE_WARNINGS')`.

**Delete**: `_WarningAwareDocTest`, the `warning_policy` callback parameter,
`_detect_warning_policy_from_options` (name-sniffing is doctestplus knowledge
laundered through the stdlib registry), and the `_stdlib_compat_line_map`
attribute stash. The `_part_context` extension point stops being a
cross-package contract.

### 3.2 Structured per-example option intake — no source-text injection

`from_examples` currently appends `# xdoctest: +SKIP` text to the first source
line of skipped examples. That corrupts source *content* (matters for
doctestplus `FIX` / `--doctest-plus-generate-diff`, and for failure display).
`DoctestPart` already accepts provided directives (`_directives` short-circuits
lazy extraction), so:

- After parsing the reconstructed docsrc, map each part back to its input
  example via the existing line map (kept **local** to `_build_docsrc`, not
  stashed on the DocTest).
- For each example, translate its `options` dict through the codec into
  `Directive` objects (`SKIP`, runtime-key-bound flags, checker-only flags)
  and attach them to the part structurally.

Source stays byte-identical to what the user wrote. This one mechanism
subsumes SKIP, warnings, FLOAT_CMP-per-example, and anything registered later.

### 3.3 Native checker fast path — no flags round-trip in the default path

`checker.check_output` currently packs `RuntimeState → optionflags int`,
resolves the facade `OutputChecker`, which unpacks `int → RuntimeState` again —
on **every** check, in stock xdoctest usage, instantiating a checker per call.
Fix:

- If the selected checker name is `'xdoctest'`, call
  `_xdoctest_check_output(got, want, runstate)` directly.
- Conversion + facade dispatch happens only when a foreign checker is
  selected (the actual boundary). Cache resolved checker instances.
- Same fast path for `GotWantException.output_difference`; replace the
  method-identity check with "foreign checkers define `output_difference` or
  they get native rendering" (don't define it on the facade base class).

This honors "structured RuntimeState is the internal truth" and removes a
perf/lossiness hazard from the default path.

### 3.4 `__doctest_skip__` / `__doctest_requires__`: keep, but hoist and cache

Keep native support (it's a widely-used ecosystem convention and a genuine
xdoctest feature; scipy/astropy users benefit under plain `--xdoctest`). Fix
the placement:

- `_apply_module_doctest_metadata` is currently called **once per part inside
  the run loop**, and the `modpath` branch does a full static AST parse of the
  module file per part. Evaluate once per `DocTest` (cache on the instance;
  cache static parses per modpath), before the part loop — or better, expose
  it to the plugin at collection time so pytest reports SKIPPED with a reason.
- `packaging` must stay optional: name-only requirements should work via
  `find_spec`/`importlib.metadata` without it; only specifier-bearing
  requirements need `packaging`, and lacking it should be a clear skip-reason
  or warning, not a hard ImportError at runtime.
- No conflict with doctestplus ownership: under the doctestplus backend,
  doctestplus applies these at collection and xdoctest's native pass is a
  harmless no-op re-check.

### 3.5 Coexistence and embedding hygiene

- **Textfile deference**: when doctestplus is active, xdoctest's plugin should
  not collect `.rst`/`.txt` files (today xdoctest's textfile collector races
  doctestplus and wins for direct-file invocations — the demo README documents
  this wart instead of fixing it). One guard in xdoctest's
  `pytest_collect_file`.
- **`XDoctestItem` must be embeddable**: it currently requires the
  `xdoctest_namespace` fixture from xdoctest's own plugin, so the doctestplus
  backend silently breaks under `-p no:xdoctest`/plugin-autoload-off. Make the
  fixture lookup defensive (fall back to `{}`), and treat
  `XDoctestItem.from_parent(parent, name=..., dtest=...)` as a supported,
  documented constructor for embedders.
- **Skip outcome mapping**: an all-parts-skipped / metadata-skipped DocTest
  must surface as a pytest *skip* with reason, not a pass (fixes the demo's
  "`skip_me` PASSED" wart from the xdoctest side too).

### 3.6 One public namespace

Three modules (`directive_facade`, `checker_facade`, `stdlib_compat`) plus ~20
new top-level `xdoctest.__init__` re-exports is too much surface to ask a
third party to trust. Consolidate the *documented* contract to one namespace —
`xdoctest.interop` (implementation modules stay put) — exposing exactly:

```python
xdoctest.interop.register_optionflag(name, runtime_state_key=None) -> int
xdoctest.interop.register_checker(name, checker) -> None
xdoctest.interop.from_examples(examples, *, globs, name, filename, lineno, optionflags, config) -> DocTest
xdoctest.interop.from_stdlib_doctest(test, *, optionflags, config) -> DocTest
```

plus the documented config keys `output_checker: str` and
`output_checker_flags: int`. Everything else is internal. Keep the top-level
re-exports minimal (`register_optionflag`, `register_checker` at most).

## 4. doctestplus changes: late lowering instead of a neutral object layer

The `DoctestPlusExample`/`DoctestPlusTest` dataclasses were meant to be the
backend-neutral truth, but in practice both backends immediately
`to_stdlib()` and consult raw option bits; the semantic fields are inferred
*from* the bits and (except `warning_policy`, which is itself redundant with
the bits) never consumed. `original_source`, `line_map`, `is_synthetic_setup`
are dead.

**The stdlib `doctest.DocTest` is already the lingua franca — use it as the
neutral representation.** What actually needs to move is *when* backend-specific
lowering happens:

- `DocTestParserPlus` / `DocTestFinderPlus` **annotate only**: option bits on
  examples, plus a small per-test metadata record
  (`skip_reason: str | None`, unmet-requirements info) instead of mutating
  source or inserting synthetic `pytest.skip()` examples.
- `backend.make_item(parent, stdlib_test, meta, *, optionflags)` does all
  lowering:
  - **StdlibBackend** (default, behavior-preserving): applies today's warning
    source rewrites, inserts the synthetic warning-context and
    skip/module-check setup examples, builds `DebugRunnerPlus`, yields
    pytest's `DoctestItem`. Bit-for-bit current behavior.
  - **XdoctestBackend**: `interop.from_stdlib_doctest(...)` with
    `config={'output_checker': 'doctestplus'}`; `meta.skip_reason` becomes a
    pytest skip on the item (correct SKIPPED outcome — fixes the demo wart);
    requirements checks run at item setup. No source rewriting anywhere.

This deletes the dataclass layer (or shrinks it to the tiny `meta` record) and
removes the inert stdlib → neutral → stdlib round-trip, while achieving what
the neutral layer was *for*.

Concrete cleanups that fall out:

- Backend selection via a `{name: factory}` registry (the `name` class attr is
  currently written and never read); keep the `--doctest-plus-backend` /
  `doctest_plus_backend` option shape as-is.
- **Do not monkeypatch `doctest.OutputChecker` when the xdoctest backend is
  selected** (it currently still happens — one of the advertised benefits of
  the backend is not doing this).
- rtol/atol: register a configured checker *instance*
  (`register_checker('doctestplus', XdoctestCompatChecker(rtol=..., atol=...))`)
  at backend init, instead of mutating class attributes on every `make_item`
  under a bare `except Exception`.
- Delete: unused `import xdoctest as xd`, dead `ignore_context`/`show_context`
  params on `_apply_warning_source_rewrites`, the no-op
  IGNORE_WARNINGS/SHOW_WARNINGS `elif` branches in `DocTestParserPlus.parse`,
  leftover factory-scope imports in `make_doctest_module_plus_class`, and the
  `configure_module_globals` module-global injection (pass config explicitly).

## 5. The pitch to doctestplus upstream

What they gain by flipping one flag:

- Precise failure line numbers (no wrapper source), part-level reporting,
  colored diffs, multiline statements, async doctests.
- **No global `doctest.OutputChecker` monkeypatch.**
- Their directives/flags keep working: same flag *bits* (the registry defers
  to `doctest.register_optionflag`), same RST language, same collection,
  same skip/requires semantics.

What they must maintain: one optional module (~150 lines) calling four
documented, semver-stable entry points — plus the late-lowering refactor,
which is justifiable to them on its own terms (it makes their own stdlib path
more explicit about where source rewriting happens).

**Conformance strategy** (the thing that builds upstream trust): parametrize
doctestplus's existing test suite over the backend (env var or `--doctest-
plus-backend` in a tox env) so the xdoctest backend inherits their entire
regression suite. Maintain an explicit divergence ledger (backend-keyed
xfails) for known gaps — e.g. `--doctest-plus-generate-diff` unsupported under
xdoctest initially.

## 6. Migration stages (each independently reviewable)

xdoctest repo:

1. `feat: native IGNORE_WARNINGS / SHOW_WARNINGS runtime directives`
   (§3.1; includes runner context handling + tests; standalone value).
2. `refactor: structured per-part option intake in stdlib_compat`
   (§3.2; delete `_WarningAwareDocTest`, callback, name-sniffing, text
   injection; line-number + source-fidelity tests).
3. `perf: native checker fast path, cache checker instances` (§3.3).
4. `fix: hoist and cache module doctest metadata; optional packaging` (§3.4;
   plus collection-time skip reporting).
5. `fix: textfile deference + embeddable XDoctestItem` (§3.5).
6. `docs: xdoctest.interop public contract` (§3.6).

doctestplus submodule:

7. `refactor: late backend lowering; parser/finder annotate only` (§4; the
   dataclass layer collapses into `meta`; stdlib behavior bit-preserved).
8. `feat: xdoctest backend v2` (skip-as-item-outcome, no monkeypatch,
   checker instance config, registry dispatch, dead-code removal).
9. `test: run doctestplus suite under both backends; divergence ledger`.

Then: update demos (drop the two README warts — skip-reporting note and the
rst-direct-invocation caveat — by fixing them), refresh the submodule pointer,
and draft the upstream PR description around §5.

## 7. Line-number / fidelity invariants (test matrix)

For both a module docstring and an RST file, under the xdoctest backend:

- failure in example N reports the original file line of the failing
  *statement* (not example start, not wrapper code);
- multi-line statement failures point inside the statement;
- `IGNORE_WARNINGS`/`SHOW_WARNINGS` active → source in the failure report is
  byte-identical to user source;
- skipped example under `__doctest_skip__` → pytest SKIPPED with reason;
- `# doctest: +FLOAT_CMP` inline comment survives reconstruction and applies
  (the directive regex accepts `x?doctest:` — inline stdlib comments parse
  natively).

## 8. Known open questions

- `--doctest-plus-generate-diff` under the xdoctest backend: defer (ledger
  entry) or implement against xdoctest's got/want records later.
- Whether xdoctest's native `__doctest_skip__` support should be gated behind
  a config knob for strict-compat users (default on seems fine).
- `IGNORE_OUTPUT` now exists both as an xdoctest runtime key and as a
  doctestplus checker short-circuit — dedupe toward the runtime key.

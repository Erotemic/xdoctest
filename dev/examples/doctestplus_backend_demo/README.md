# doctestplus xdoctest-backend demo

This demo proves that `pytest --doctest-plus --doctest-plus-backend=xdoctest`:

1. Keeps doctestplus collection: RST directives, `__doctest_skip__`,
   `__doctest_requires__`, and the doctestplus output checker (FIX,
   FLOAT_CMP, IGNORE_OUTPUT, ALLOW_BYTES, ...).
2. Delegates execution to xdoctest's runner so failure reporting, async, and
   `# xdoctest: +DIRECTIVES` work natively — without rewriting example
   source or monkeypatching `doctest.OutputChecker`.

## Run

From the xdoctest repo root:

```bash
# Default stdlib backend (historical doctestplus behavior)
pytest dev/examples/doctestplus_backend_demo/sample_pkg/ -rs

# Opt in to the xdoctest backend
pytest dev/examples/doctestplus_backend_demo/sample_pkg/ \
    --doctest-plus-backend=xdoctest -rs
```

Both invocations collect and run the same tests with the same outcomes. The
directory contains a local `pytest.ini` (`--doctest-plus --doctest-glob=*.rst`)
so the parent xdoctest project's `--xdoctest` default doesn't apply.

## What you should see

```
$ pytest sample_pkg/ -rs
collected 5 items
sample_pkg/mod.py::sample_pkg.mod.fix_me PASSED
sample_pkg/mod.py::sample_pkg.mod.float_cmp PASSED
sample_pkg/mod.py::sample_pkg.mod.ignore_warnings PASSED
sample_pkg/mod.py::sample_pkg.mod.skip_me SKIPPED (listed in `__doctest_skip__`)
sample_pkg/narrative.rst::narrative.rst PASSED

$ pytest sample_pkg/ --doctest-plus-backend=xdoctest -rs
collected 5 items
sample_pkg/mod.py::sample_pkg.mod.fix_me PASSED
sample_pkg/mod.py::sample_pkg.mod.float_cmp PASSED
sample_pkg/mod.py::sample_pkg.mod.ignore_warnings PASSED
sample_pkg/mod.py::sample_pkg.mod.skip_me SKIPPED (listed in `__doctest_skip__`)
sample_pkg/narrative.rst::narrative.rst PASSED
```

The two runs are outcome-identical. Under the xdoctest backend:

- `fix_me` proves the doctestplus output checker (`+FIX`) is wired into
  xdoctest's runner via `pytest_doctestplus.xdoctest_compat`.
- `float_cmp` proves `+FLOAT_CMP` matching works.
- `ignore_warnings` proves warning policy is honored — by xdoctest's runner,
  without rewriting the example source.
- `skip_me` proves module-level `__doctest_skip__` is honored *and reported
  as a proper pytest skip with a reason* (not silently passed).
- `narrative.rst` proves doctestplus' RST directive language
  (`.. doctest-skip::`) still drives skip semantics while xdoctest executes.

## Notes

- The RST file works whether you point pytest at the directory or at the
  `.rst` file directly: when doctestplus is active, xdoctest's textfile
  collector defers so doctestplus' RST parser owns `.rst`/`.txt` files.
- `--doctest-plus-generate-diff` is stdlib-backend only; see
  `tpl/pytest-doctestplus/DIVERGENCES.md` for the full backend divergence
  ledger.

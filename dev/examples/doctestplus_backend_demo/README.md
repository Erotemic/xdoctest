# doctestplus xdoctest-backend demo

This demo proves that `pytest --doctest-plus --doctest-plus-backend=xdoctest`:

1. Keeps doctestplus collection: RST directives, `__doctest_skip__`,
   `__doctest_requires__`, the doctestplus output checker (FIX, FLOAT_CMP,
   IGNORE_OUTPUT, ALLOW_BYTES, ...).
2. Delegates execution to xdoctest's runner so failure reporting, async,
   and `# xdoctest: +DIRECTIVES` work natively.

## Run

From the xdoctest repo root:

```
# Default stdlib backend (unchanged behavior)
pytest --doctest-plus dev/examples/doctestplus_backend_demo/sample_pkg/

# Opt in to the xdoctest backend
pytest --doctest-plus --doctest-plus-backend=xdoctest dev/examples/doctestplus_backend_demo/sample_pkg/
```

Both invocations should pass the same collected tests. The xdoctest path
exercises:

- A doctestplus checker flag (`# doctest: +FIX`) on a `.py` doctest, which
  proves the doctestplus checker is wired into xdoctest's runner.
- An RST narrative file with a `.. doctest-skip::` directive, which proves
  doctestplus' RST parsing still drives skip semantics under the xdoctest
  backend.
- A module-level `__doctest_skip__` to confirm doctestplus' module-level
  filters still apply.

## What you should see

```
$ cd dev/examples/doctestplus_backend_demo && pytest sample_pkg/
collected 4 items
sample_pkg/mod.py::sample_pkg.mod.fix_me PASSED
sample_pkg/mod.py::sample_pkg.mod.float_cmp PASSED
sample_pkg/mod.py::sample_pkg.mod.skip_me SKIPPED (listed in `__doctest_skip__`)
sample_pkg/narrative.rst::narrative.rst PASSED

$ cd dev/examples/doctestplus_backend_demo && pytest sample_pkg/ --doctest-plus-backend=xdoctest
collected 4 items
sample_pkg/mod.py::sample_pkg.mod.fix_me PASSED
sample_pkg/mod.py::sample_pkg.mod.float_cmp PASSED
sample_pkg/mod.py::sample_pkg.mod.skip_me PASSED   # see note below
sample_pkg/narrative.rst::narrative.rst PASSED
```

The directory contains a local `pytest.ini` so the parent xdoctest project's
`--xdoctest` default doesn't apply.

**Note on skip reporting:** Under the xdoctest backend, doctestplus' module-
level `__doctest_skip__` still prevents the body from executing — but
xdoctest's runner reports the synthetic `pytest.skip()` example as a graceful
test exit ("PASSED") rather than as a pytest skip outcome. The user's
intent is honored (the failing body never runs); only the reporting label
differs. Translating xdoctest's exit-test outcome to a pytest skip is a
follow-up.

**Important:** Always run pytest with the directory as the argument, not a
single `.rst` file. When an `.rst` file is the init path, xdoctest's textfile
collector grabs it before doctestplus does, bypassing the RST directive
language.

The `skip_me` skip comes from `__doctest_skip__`; the rst test passes because
its inner skip directive is honored by doctestplus' parser; the FIX checker
flag is provided by the doctestplus output checker now plugged into xdoctest's
matcher via the `register_with_xdoctest()` helper.

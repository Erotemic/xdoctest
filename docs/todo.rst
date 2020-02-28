Tasks: 
------

This module is in a working state. It is nearly complete, but there are a few
todo items: 

Extraction:
^^^^^^^^^^^
-  [x] Parse freeform-style doctest examples (builtin-doctest default)
-  [x] Parse google-style doctest examples explicitly
-  [ ] Parse numpy-style doctest examples explicitly


Parsing:
^^^^^^^^

-  [X] Removed all known syntax backwards incompatibility. 
-  [ ] Removed all known directive backwards incompatibility. 

Checking:
^^^^^^^^^

-  [x] Support got/want testing with stdout.
-  [x] Support got/want testing with evaluated statements.
-  [x] Support got/want testing with ``NORMALIZED_WHITESPACE`` and
   ``ELLIPSES`` by default
-  [x] Support toggling got/want directives for backwards compatibility?
-  [x] Support got/want testing with exceptions.

Reporting:
^^^^^^^^^^

-  [x] Optional colored output
-  [x] Support advanced got/want reporting directive for backwards
   compatibility (e.g udiff, ndiff)

Running:
^^^^^^^^

-  [x] Standalone ``doctest_module`` entry point.
-  [x] Plugin based ``pytest`` entry point.
-  [x] Defaults to static parsing doctests
-  [x] Ability to dynamically parse doctests
-  [x] Can run tests in extension modules
-  [ ] Add dynamic parsing to pytest plugin

Directives
~~~~~~~~~~

-  [x] multi-line directives (new feature, not in doctest)
-  [x] ``# doctest: +SKIP`` inline directive
-  [x] ``# doctest: +SKIP`` global directive
-  [x] ``# doctest: -NORMALIZED_WHITESPACE`` inline directive
-  [x] ``# doctest: -ELLIPSES`` inline directive
-  [x] ``# doctest: +REPORT_NDIFF`` inline directive
-  [x] ``# doctest: +REPORT_UDIFF`` inline directive

Testing:
^^^^^^^^

-  [x] Tests of core module components
-  [x] Register on pypi
-  [x] CI-via Travis
-  [x] CI-via AppVeyor
-  [x] Coverage
-  [ ] Add a small pybind11 extension module that demonstrates how tests
   can be defined and run in extension modules
-  [ ] 95% or better coverage (note reported coverage is artificially
   small due to issues with coverage of pytest plugins)

Documentation:
^^^^^^^^^^^^^^

-  [x] Basic docstring docs
-  [x] Basic readme
-  [x] Improve readme
-  [X] Further improve readme
-  [X] Auto-generate read-the-docs Documentation
-  [X] Getting Started documentation in read-the-docs


Uncategorized:
^^^^^^^^^^^^^^

-  [x] Make a new default mode: auto, which first tries google-style,
   and then fallback to freeform mode if no doctests are found or if an
   error occurs. (new in 0.4.0)
- [x] multi-part got / want "delayed" matching (new in 0.4.0). 
- [x] fix the higlighting of the "got" string when dumping test results (new in 0.4.0)
- [ ] Write a plugin to sphinx so it uses xdoctest instead of doctest?
- [ ] Attempt to get pytorch branch merged: https://github.com/pytorch/pytorch/pull/15648

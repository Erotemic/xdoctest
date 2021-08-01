# Changelog

We are currently working on porting this changelog to the specifications in
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## Version 0.15.6 - Unreleased


### Changed
* Directive syntax errors are now handled as doctest runtime errors and return
  better debugging information.


## Version 0.15.5 - Released 2021-06-27

### Changed
* Better message when a pytest skip or exit-test-exception occurs

### Fixed
* Suppressed warning about using internal `FixtureRequest`


## Version 0.15.4 - Released 2021-01-29

### Fixed
* Minor issues with release tarballs. 


## Version 0.15.3 - Released 2021-01-28

### Fixed
* Color issues on win32


### Changed
* Moved to CircleCI deploy scripts


## Version 0.15.2 - Released 2021-01-28

### Fixed
* Bug where references to doctest variables were never released


## Version 0.15.1 - Released 2021-01-28

### Added
* Documentation improvements
* Minor text fixes


## Version 0.15.0 - Released 2020-09-11


### Added
* `pip install xdoctest` can now specify `[colors]` or `[jupyter]`
* Enhanced REQUIRES directive behavior, multiple comma-separated requirements
  can now be listed in one directive.
* Xdoctest can now be run inside of Jupyter notebooks / IPython sessions
* Xdoctest can now be run on Jupyter notebooks (Note that in general it is
  better practice to write a module)

### Fixed
* Bug in `doctest_callable` where it would not populate globals from the function context.

### Changed
* Renamed `Config` to `DoctestConfig`
* Renamed `static_analysis.parse_calldefs` to `static_analysis.parse_static_calldefs`. 
  A temporary function with the old name is exposed for backwards compatibility.
* Changed argument name from `modpath_or_name` to `module_identifier` in several functions.
  This is to better indicate its coercible nature as either a module path, a
  module name. This change impacts `doctest_module`, `parse_doctestables`,
  `package_calldefs`. 


## [Version 0.14.0] - Released 2020-08-26 

###  Added
* The REQUIRES directive can now inspect existence or values of environment variables.
* Added top-level `doctest_callable` function, which executes the doctests of a
  function or class.
* Support for `NO_COLOR` environment variable.

###  Fixed
* `IPython.embed` and `ipdb.launch_ipdb_on_exception` now correctly work from
  inside doctests.
* Small incompatibility with `pytest-matrix`. See #82

## [Version 0.13.0] - Released 2020-07-10  

###  Changed
* `xdoctest.runner.doctest_module` now accepts the module object itself.
* Zero-args doctests no longer capture stdout (this prevents IPython embedding issues).

###  Fixed
* Fixed minor bug in zero args runner when captured stdout is None
* We now ignore doctests in setters and deleters to prevent them from clobbering doctests in getters.


## [Version 0.12.0] - Released 2020-04-16 

###  Added
* CLI support for doctest "analysis" mode (which can be either static or dynamic). 

###  Fixed
* Google docstrings now allow for leading whitespace in the description.
* Support python `3.9.0a5` when `eval` returns a coroutine (tentative).
* Use `from_parent` constructors for `pytest` modules when possible. Fixes deprecation warning.


### TODO
* better docs
* support for numpy and RST example blocks
* make `xdoctest -m xdoctest.__init__ __doc__:0` work like `xdoctest -m xdoctest/__init__.py __doc__:0` 


## [Version 0.11.0] - Released 2019-12-18

### Added
* Add CI support for PyPy
* Add CI support for CPython 3.8
* Added tox
* REQUIRES directive now supports CPython, IronPython, Jython, and PyPy
* REQUIRES directive now supports PY2, PY3


## [Version 0.10.3] - Released 2019-11-14

### Fixed
* The verbose flag was previously not taken into account. This is now fixed.


## [Version 0.10.2] - Released 2019-11-12

### Changed
* The `--xdoc-glob` list of patterns now defaults to empty.  In general it is
  not safe to assume a default pattern. This means the user must opt-in to
  testing text files as if they were doctests.


## [Version 0.10.1] - Released 2019-10-31

### Changed
* `PythonPathContext` now works in more corner cases, although some rarer
  corner cases will now break. This trade-off should be a net positive. 
* Releases are handled by TravisCI and will be signed with the GPG key 98007794ED130347559354B1109AC852D297D757 (note we will rotate this key in 1 year).


## [Version 0.10.0] - Released 2019-08-15

### Added
* Can now specify zero-args as the command to the xdoctest CLI to run all zero-args functions in a file.  
* Add known issue: note about possible want-reporting bug.
* More docstrings
* Add `--version` option to CLI interface

### Changed 
* Improved backwards compatibility. Explicit continuations now work more similarly to the original doctest. 
* You no longer need a comment to denote that a `...` is a continuation and not a ellipsis.
* Want statements will check against return values in nested continuations
* Cleaned up internal code, private APIs may break.
* Failed doctests will now print their original line prefixes (either `>>> ` or `... ` when possible)

### Fixed
* `run_tests.py` now returns the correct error code. (fixes CircleCI)
* Fixed outdated docs in the directive file


## [Version 0.9.1] - Released 2019-07-16


### Changed 
* Improved backwards compatibility. Explicit continuations now work more similarly to the original doctest. 
* You no longer need a commend to denote that a `...` is a continuation and not a ellipsis.
* Want statements will check against return values in nested continuations

### Fixed
* Removed debug print


## [Version 0.9.0] - Released 2019-07-16

### Added
* Add skip count to the native runner

### Changed
* Renamed several functions in various classes to be private. Its unlikely anyone was externally using them. The change functions include:

    * `DoctestExample`: `pre_run` -> `_pre_run` 
    * `DoctestExample`: `post_run` -> `_post_run` 
    * `Directive`: `unpack_args` -> `_unpack_args` 
    * `Directive`: `state_item` -> `effect` 

* Modified behavior of `RuntimeState.update` to use the directive effect.

* Added explicit REQUIRES runtime-state, which maintains a set of unmet
  conditions. When non-empty it behaves like SKIP.

### Fixed
* The REQUIRES directive no longer clobbers the previous SKIP state.


## [Version 0.8.3] - Released 2019-07-15

### Fixed
* The native runner now exits with a non-zero error code on failure

## [Version 0.8.2] - Released 2019-07-14

### Changed
* Slight modifications to file structure
* Inherit `util_import` from `ubelt`

### Fixed
* Fixed issue with nested functions and exec in older python versions
* Fixed issue in modsplit with multidot suffixes.

## [Version 0.8.1] - Released 2019-05-24

### Fixed

* Minor fixes to readme and docs

## [Version 0.8.0] - Released 2019-05-03

### Added
* Added docs! Finally!

### Fixed
* Got-want exceptions now return a special error if it fails to create a string-representation of the object instead of crashing.
* The `index` argument in `import_module_from_path` is now correctly used.

## [Version 0.7.3] - Released 2019-03-21

### Added
* The REQUIRES directive can now accept python modules in the form: `# xdoctest: +REQUIRES(module:<my_modname>)`
* Support for double-colon example syntax in google style parsing: e.g. `Example::`.

### Changed
* Demo folder illustrating how xdoctest formats error messages
* Reduced import overhead time from 20ms to 1ms.


## [Version 0.7.2] - Released 2019-02-02

### Changed
* Removed warning if `pygments` is not installed


## [Version 0.7.1] - Released 2019-02-01

### Changed
* Changed verbosity defaults


## [Version 0.7.0] - Released 2019-01-18

### Added
* Added `global-exec` to native xdoctest CLI and `xdoctest-global-exec` to the `pytest` plugin CLI

### Changed
* Renamed `DocTest.globs` to `DocTest.global_namespace`
* Internal test changes

### Fixed
* Fixed issue in `traceback` parsing that sometimes caused incorrectly offset line numbers.


## [Version 0.6.2] - Released 20l8-12-11

### Fixed
* Fixed bug in `static_analysis.is_balanced_statement` and
  `static_analysis.extract_comments` having to do with empty lines
* Fixed odd corner case where `import_module_from_path` seemed to modify `sys.path` in a specific environment
* Fixed Python2 future issues using the print name in doctests.
* Added option to print test times in the runner.


## [Version 0.6.1] - Released 2018-11-15

### Fixed
* Fixed python2 unicode error in collection phase


## [Version 0.6.0] - Released 2018-10-23

### Added
* Added nocolor command line arg
* Added parserkw arg
* Python 3.7 support

### Changed
* Better error messages when you forget a raw string on a google block with newlines in the docstr.
* Tests for malformed google docstr case.


## [Version 0.5.8]

### Fixed
* Fixed install issues (/introduced hack FIXME later)
* Fixed issue with raw string lineno parsing

## [Version 0.5.0] - Released 2018-07-14

### Added
* Added config option for lineno offsets. (corresponding arguments added to
  native and pytest runners)
* Partial support for Python 3.7


### Changed
* Generally Improved doctest error reporting 
    * Includes better coloring for quick visual inspection
    * Line numbers are now reported in a more intuitive way
    * We finally removed the exec `DoctestExample.run` from the traceback!
    
* (we report line numbers of errors in a more intuitive way).

### Fixed
* Fixed GH#20 where `doclineno_end` was incorrectly parsed
* Fixed issue where google style block lineno was incorrect

## [Version 0.4.1]

### Fixed
* Fixed bug with reporting elapsed time in native runner


## [Version 0.4.0] - Released 2018-06-10

### Added
* Added auto parsing style. This first tries to use Google, but falls back on
  freeform if no google-style doctests are found.
* Errors are no longer printed twice if only a single test is being run.
* Added command "dump" to native runner that reformats enabled doctests so they
  can be run as unit tests.
* Implemented delayed want matching. This enables doctests to use multiple
  print statements in a row and use a single want statement to check all of
  their output.

### Changed
* All parsers now default to the new "auto" style.
* Colorized doctest now highlights "want" lines in a distinct (green) color

## [Version 0.3.5] - Released 2018-06-03

### Changed
* Changed development status to Beta
* Output difference now strips the `BLANKLINE` marker if enabled

## [Version 0.3.4] - Released 2018-05-27

### Changed
* The reported difference between got and want now preserves newlines for
  better visibility.

## [Version 0.3.3] - Released 2018-05-13

### Fixed
* Fixed bug where pytest would collect all tests twice 
  (because the `__init__.py` file was normalized to a directory in `package_modpaths`)

## [Version 0.3.2] - Released 2018-05-08

### Added
* API update to facilitate `mkinit`

## [Version 0.3.1] - Released 2018-04-20

### Added
* Improved doctest syntax error message
* `PythonPathContext` no longer breaks if small changes to the path occur in its context.
* `PythonPathContext` can now insert into front or back of sys.path
* Flags can now be specified before or after positional arguments when using the __main__ script

## [Version 0.3.0] - Released 2018-04-02

### Added
* Added entry point script
* example command lines now use the full path if the module is not in the `PYTHONPATH`
* Can now override `sys.path` when calling `modname_to_modpath` and `is_modname_importable` (API change)

## [Version 0.2.4]  - Released 2018-03-27

### Added
* added `IGNORE_WANT` directive
* added separator between printout of docsrc and its stdout

## [Version 0.2.3]

### Changed
* Print correct doctest line number in the traceback
* Runner `on_error` will now default to return instead of raise

## [Version 0.2.2]

### Fixed
* Fixed option parsing bug in __main__ script


## [Version 0.2.1]

### Added
* The default runtime state can be customized with the `xdoc-options` command line argument.

### Fixed
* Fix crash when trying to read binary files
* Fix issue in `_docstr_line_workaround`


## [Version 0.2.0] - Released 2018-02-20

### Added
* Starting keeping a changelog, all changes before this point are only
  documented via the git history.

## [Version 0.1.0] - Released 2018-02-04

### Added
* Undocumented changes


## [Version 0.0.12] - Released 2017-12-29

### Added
* Undocumented changes


## [Version 0.0.1] - Released 2017-09-24

### Added
* First release

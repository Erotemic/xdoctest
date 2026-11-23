# Agent Instructions

- Module source is in `src/xdoctest`.
- New unit tests go in `tests`.
- Follow PEP 8.
- Prefer explanatory docstrings for API level documentation.
- Use rst files in `docs/source/manual` for narrative documentation. 
- Use `run_tests.py` for unit tests and only.
- Use `run_doctests.sh` for doctests only.
- Dependencies are listed in `requirements/*.txt` and mirrored in `pyproject.toml` optional extras; keep both synchronized.

## Commit attribution

Every agent-authored commit must carry a `Co-authored-by:` trailer naming the exact model (and weights/config variant, when known) that produced it, per its own runtime identification — never copied from earlier commits; if undeterminable, say so. For qwen models, the appropriate email is: <noreply@alibabacloud.com> 

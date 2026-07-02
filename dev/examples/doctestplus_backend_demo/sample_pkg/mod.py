"""
Sample module exercising doctestplus features under either backend.

Module-level filter: ``__doctest_skip__`` causes ``skip_me`` to be skipped
during collection, regardless of which execution backend is active.
"""

__doctest_skip__ = ['skip_me']


def fix_me():
    """
    Uses the doctestplus FIX checker rule (strip trailing ``L``).
    Will fail under stdlib without the doctestplus checker. With either the
    default stdlib backend or the xdoctest backend (which registers the
    doctestplus checker with xdoctest's pluggable checker registry), this
    passes.

    Example:

        >>> print('10')  # doctest: +FIX
        10L
    """


def skip_me():
    """
    Skipped by the module-level ``__doctest_skip__``. The body of this
    docstring would otherwise fail.

    Example:

        >>> 1 / 0
        nope
    """


def float_cmp():
    """
    Uses the FLOAT_CMP checker rule. Both backends understand it.

    Example:

        >>> import math
        >>> print(math.pi)  # doctest: +FLOAT_CMP
        3.141593
    """


def ignore_warnings():
    """
    Uses IGNORE_WARNINGS. Under the stdlib backend this is implemented by
    rewriting the example source to wrap it in a context manager; under the
    xdoctest backend the runner silences warnings without touching source,
    so failure line numbers stay accurate. Either way, the noisy warning
    does not cause the doctest to fail.

    Example:

        >>> import warnings
        >>> warnings.warn('this is noisy')  # doctest: +IGNORE_WARNINGS
        >>> print('quiet')
        quiet
    """

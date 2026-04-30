"""
Example module demonstrating doctestplus compatibility through xdoctest.

These doctests rely on the doctestplus output checker being registered with
xdoctest. They use checker-only optionflags (``FIX``, ``FLOAT_CMP``,
``IGNORE_OUTPUT``) via xdoctest directives.

Run them through ``run_demo.py``:

    python dev/examples/doctestplus_demo/run_demo.py
"""

from __future__ import annotations


def long_int_repr() -> str:
    """
    Returns the literal string ``"10"``. The want clause uses an ``L`` suffix
    that only matches under doctestplus' ``FIX`` rule.

    Example:
        >>> print(long_int_repr())  # xdoctest: +FIX
        10L
    """
    return '10'


def near_pi() -> float:
    """
    Returns a value close to pi. The want clause is approximate and only
    matches under doctestplus' ``FLOAT_CMP`` rule.

    Example:
        >>> print(near_pi())  # xdoctest: +FLOAT_CMP
        3.14159
    """
    import math
    return math.pi


def noisy() -> str:
    """
    Returns a deliberately noisy string. The want clause is a placeholder that
    only matches under doctestplus' ``IGNORE_OUTPUT`` rule.

    Example:
        >>> print(noisy())  # xdoctest: +IGNORE_OUTPUT
        whatever
    """
    return 'this output is not what the want says, but IGNORE_OUTPUT skips it'


def block_scope_demo() -> None:
    """
    Show that a doctestplus flag persists across parts when set as a block
    directive and clears when toggled off.

    Example:
        >>> # xdoctest: +FIX
        >>> print('100')
        100L
        >>> print('200')
        200L
        >>> # xdoctest: -FIX
        >>> print('300')
        300
    """

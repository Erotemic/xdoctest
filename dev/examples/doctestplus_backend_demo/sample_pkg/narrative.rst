Narrative tests
===============

This file exercises an RST-only doctestplus directive: ``.. doctest-skip::``.

A simple example that passes:

    >>> 1 + 1
    2

The next example would fail, but doctestplus' RST parser sees the
``doctest-skip`` directive and marks it for skipping. This part of the demo
proves that *doctestplus' RST directive language is still in effect* even
when execution is delegated to xdoctest's runner.

.. doctest-skip::

    >>> 1 / 0
    nope

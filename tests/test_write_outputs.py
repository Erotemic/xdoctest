"""
Unit tests for the --write-outputs and --fill-missing-wants feature.
"""

import xdoctest
import textwrap
import pytest


@pytest.fixture
def create_test_file(tmp_path):
    """
    Fixture that returns a function to create test files.
    """

    def _create_file(content):
        """Create a test Python file with the given content."""
        test_file = tmp_path / "test_doctest.py"
        test_file.write_text(textwrap.dedent(content))
        return test_file

    return _create_file


def test_write_outputs_basic(create_test_file):
    """
    Test basic write-outputs functionality.
    """

    test_file = create_test_file('''
        def example():
            """
            Example:
                >>> print('hello')
                wrong output
            """
            pass
    ''')

    xdoctest.doctest_module(
        str(test_file), command="all", config={"write_outputs": True}
    )

    assert test_file.read_text() == textwrap.dedent('''
        def example():
            """
            Example:
                >>> print('hello')
                hello
            """
            pass
    ''')


def test_write_outputs_eval(create_test_file):
    """
    Test write-outputs with eval expressions.
    """

    test_file = create_test_file('''
        def example():
            """
            Example:
                >>> 2 + 2
                5
            """
            pass
    ''')

    xdoctest.doctest_module(
        str(test_file), command="all", config={"write_outputs": True}
    )

    assert test_file.read_text() == textwrap.dedent('''
        def example():
            """
            Example:
                >>> 2 + 2
                4
            """
            pass
    ''')


def test_write_outputs_multiline(create_test_file):
    """
    Test write-outputs with multiline output.
    """

    test_file = create_test_file('''
        def example():
            """
            Example:
                >>> for i in range(3):
                ...     print(i)
                wrong
            """
            pass
    ''')

    xdoctest.doctest_module(
        str(test_file), command="all", config={"write_outputs": True}
    )

    assert test_file.read_text() == textwrap.dedent('''
        def example():
            """
            Example:
                >>> for i in range(3):
                ...     print(i)
                0
                1
                2
            """
            pass
    ''')


def test_write_outputs_indentation(create_test_file):
    """
    Test that indentation is preserved correctly.
    """

    test_file = create_test_file('''
        class MyClass:
            def method(self):
                """
                Example:
                    >>> print('test')
                    wrong
                """
                pass
    ''')

    xdoctest.doctest_module(
        str(test_file), command="all", config={"write_outputs": True}
    )

    assert test_file.read_text() == textwrap.dedent('''
        class MyClass:
            def method(self):
                """
                Example:
                    >>> print('test')
                    test
                """
                pass
    ''')


def test_fill_missing_wants(create_test_file):
    """
    Test --fill-missing-wants flag.
    """

    test_content = '''
        def example():
            """
            Example:
                >>> print('hello')
            """
            pass
    '''
    test_file = create_test_file(test_content)

    # Run without --fill-missing-wants
    xdoctest.doctest_module(
        str(test_file),
        command="all",
        config={"write_outputs": True},
    )

    assert test_file.read_text() == textwrap.dedent(test_content)

    # Now run with --fill-missing-wants
    xdoctest.doctest_module(
        str(test_file),
        command="all",
        config={"write_outputs": True, "fill_missing_wants": True},
    )

    assert test_file.read_text() == textwrap.dedent('''
        def example():
            """
            Example:
                >>> print('hello')
                hello
            """
            pass
    ''')


def test_write_outputs_skip_failed(create_test_file):
    """
    Test that tests with actual exceptions are skipped.
    """

    test_content = '''
        def example():
            """
            Example:
                >>> 1 / 0
                should not be written
            """
            pass
    '''
    test_file = create_test_file(test_content)

    xdoctest.doctest_module(
        str(test_file), command="all", config={"write_outputs": True}
    )

    assert test_file.read_text() == textwrap.dedent(test_content)




def test_write_outputs_preserves_blanklines(create_test_file):
    """
    Test that blank lines are converted to <BLANKLINE> markers.
    """
    test_file = create_test_file('''
        def example():
            """
            Example:
                >>> for i in [1, '', 3]:
                ...     print(i)
                wrong
            """
            pass
    ''')

    xdoctest.doctest_module(
        str(test_file), command="all", config={"write_outputs": True}
    )

    assert test_file.read_text() == textwrap.dedent('''
        def example():
            """
            Example:
                >>> for i in [1, '', 3]:
                ...     print(i)
                1
                <BLANKLINE>
                3
            """
            pass
    ''')


def test_write_outputs_multiple_parts(create_test_file):
    """
    Test updating parts in a single doctest.

    When a part fails, execution stops, so only the first failing part is updated.
    """
    test_file = create_test_file('''
        def example():
            """
            Example:
                >>> x = 5
                >>> print(x + 1)
                0
                >>> print(x * 2)
                wrong
            """
            pass
    ''')

    xdoctest.doctest_module(
        str(test_file), command="all", config={"write_outputs": True}
    )

    # The second doctest was not executed because the first one failed,
    # so the output is still 'wrong'
    # This is expected behavior - run --write-outputs again to update next parts
    assert test_file.read_text() == textwrap.dedent('''
        def example():
            """
            Example:
                >>> x = 5
                >>> print(x + 1)
                6
                >>> print(x * 2)
                wrong
            """
            pass
    ''')

    xdoctest.doctest_module(
        str(test_file), command="all", config={"write_outputs": True}
    )

    assert test_file.read_text() == textwrap.dedent('''
        def example():
            """
            Example:
                >>> x = 5
                >>> print(x + 1)
                6
                >>> print(x * 2)
                10
            """
            pass
    ''')


def test_write_outputs_no_modification_on_success(create_test_file):
    """
    Test that already-correct outputs are not modified.
    """

    test_content = '''
        def example():
            """
            Example:
                >>> 2 + 2
                4
            """
            pass
    '''
    test_file = create_test_file(test_content)

    xdoctest.doctest_module(
        str(test_file), command="all", config={"write_outputs": True}
    )

    assert test_file.read_text() == textwrap.dedent(test_content)


@pytest.mark.parametrize(
    "test_content, expected_spaces",
    [
        (
            '''
            def function():
                """
                Example:
                    >>> 'test'
                    wrong
                """
                pass
        ''',
            8,  # Top-level function: 4 (function) + 4 (docstring)
        ),
        (
            '''
            class Class1:
                def method(self):
                    """
                    Example:
                        >>> 'test'
                        wrong
                    """
                    pass
        ''',
            12,  # Class method: 4 (class) + 4 (method) + 4 (docstring)
        ),
    ],
)
def test_indentation_at_various_levels(create_test_file, test_content, expected_spaces):
    """
    Test indentation preservation at various nesting levels.
    """
    test_file = create_test_file(test_content)

    xdoctest.doctest_module(
        str(test_file), command="all", config={"write_outputs": True}
    )

    lines = test_file.read_text().splitlines()

    test_lines = [line for line in lines if "'test'" in line and ">>>" not in line]

    test_line = test_lines[0]
    indent_count = len(test_line) - len(test_line.lstrip())
    assert indent_count == expected_spaces


def test_write_outputs_with_eval_none(create_test_file):
    """
    Test write-outputs with expressions that evaluate to None.

    Note: Currently, when an expression evaluates to None with no stdout,
    the output is treated as empty and not written. This is a known limitation.
    """
    test_content = '''
        def example():
            """
            Example:
                >>> None
                wrong
            """
            pass
    '''
    test_file = create_test_file(test_content)

    xdoctest.doctest_module(
        str(test_file), command="all", config={"write_outputs": True}
    )

    # File should remain unchanged because got_eval=None is treated as no output
    assert test_file.read_text() == textwrap.dedent(test_content)


def test_write_outputs_empty_output(create_test_file):
    """
    Test that statements with no output don't modify the file when output is empty.
    """
    test_content = '''
        def example():
            """
            Example:
                >>> x = 5
                wrong output
            """
            pass
    '''
    test_file = create_test_file(test_content)

    xdoctest.doctest_module(
        str(test_file), command="all", config={"write_outputs": True}
    )

    # When got output is empty (""), formatted_lines will be empty
    # so _compute_part_modification returns None and file is unchanged
    assert test_file.read_text() == textwrap.dedent(test_content)


def test_fill_missing_wants_no_output(create_test_file):
    """
    Test that --fill-missing-wants doesn't add wants for statements with no output.
    """
    test_content = '''
        def example():
            """
            Example:
                >>> x = 5
            """
            pass
    '''
    test_file = create_test_file(test_content)

    xdoctest.doctest_module(
        str(test_file),
        command="all",
        config={"write_outputs": True, "fill_missing_wants": True},
    )

    # Should not add output for assignment statements
    assert test_file.read_text() == textwrap.dedent(test_content)

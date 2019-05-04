
def mwe():

    # TODO: show that sphinx fails to parse this, and use xdoctest to make
    # things better.

    # This used to be a perfectly valid docstring in xdoctest, but I've since
    # changed it so it doesn't cause sphinx problems.
    docstring = r"""

    Example:
        >>> from xdoctest import core
        >>> from xdoctest import utils
        >>> docstr = utils.codeblock(
                '''
                freeform
                >>> doctest
                >>> hasmultilines
                whoppie
                >>> 'butthis is the same doctest'

                >>> secondone

                Script:
                    >>> 'special case, dont parse me'

                DisableDoctest:
                    >>> 'special case, dont parse me'
                    want

                AnythingElse:
                    >>> 'general case, parse me'
                   want
                ''')
        >>> examples = list(parse_freeform_docstr_examples(docstr, asone=True))
        >>> assert len(examples) == 1
        >>> examples = list(parse_freeform_docstr_examples(docstr, asone=False))
        >>> assert len(examples) == 3
    """

    print('docstring = {!r}'.format(docstring))
    # pass this to sphinx and show it breaks because whitespace is not added to
    # pad between the lines, even though they should share lexical scope.
    # Some people say whitespace is not syntax. They are half-correct.
    # It should not count as Python syntax if its a blank line with no
    # trailing non-space characters (unless its wrapped in string quotes).
    # Spaces are great syntax, but only when they have non-space content after
    # them.

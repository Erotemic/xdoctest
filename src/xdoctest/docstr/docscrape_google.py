"""
Handles parsing of information out of google style docstrings

It is not clear which of these `GoogleStyleDocs1`_ `GoogleStyleDocs2`_ is *the*
standard or if there is one.

This code has been exported to a standalone package

    * https://github.com/Erotemic/googledoc

This is similar to:

    * https://pypi.org/project/docstring-parser/
    * https://pypi.org/project/numpydoc/

It hasn't been decided if this will remain vendored in xdoctest or pulled in as
a dependency.

References:
    .. [GoogleStyleDocs1] https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html#example-google
    .. [GoogleStyleDocs2] http://www.sphinx-doc.org/en/stable/ext/example_google.html#example-google
"""
import re
import textwrap
import collections
from xdoctest import exceptions
from xdoctest.utils.util_str import ensure_unicode

DocBlock = collections.namedtuple('DocBlock', ['text', 'offset'])


def split_google_docblocks(docstr):
    """
    Breaks a docstring into parts defined by google style

    Args:
        docstr (str): a docstring

    Returns:
        List[Tuple[str, DocBlock]]:
            list of 2-tuples where the first item is a google style docstring
            tag and the second item is the bock corresponding to that tag. The
            block itself is a 2-tuple where the first item is the unindented
            text and the second item is the line offset indicating that blocks
            location in the docstring.

    Note:
        Unknown or "freeform" sections are given a generic "__DOC__" tag.
        A section tag may be specified multiple times.

    CommandLine:
        xdoctest xdoctest.docstr.docscrape_google split_google_docblocks:2

    Example:
        >>> from xdoctest.docstr.docscrape_google import *  # NOQA
        >>> from xdoctest import utils
        >>> docstr = utils.codeblock(
        ...     '''
        ...     one line description
        ...
        ...     multiline
        ...     description
        ...
        ...     Args:
        ...         foo: bar
        ...
        ...     Returns:
        ...         None
        ...
        ...     Example:
        ...         >>> print('eg1')
        ...         eg1
        ...
        ...     Example:
        ...         >>> print('eg2')
        ...         eg2
        ...     ''')
        >>> groups = split_google_docblocks(docstr)
        >>> assert len(groups) == 5
        >>> [g[0] for g in groups]
        ['__DOC__', 'Args', 'Returns', 'Example', 'Example']

    Example:
        >>> from xdoctest.docstr.docscrape_google import *  # NOQA
        >>> docstr = split_google_docblocks.__doc__
        >>> groups = split_google_docblocks(docstr)

    Example:
        >>> from xdoctest.docstr.docscrape_google import *  # NOQA
        >>> from xdoctest import utils
        >>> docstr = utils.codeblock(
        ...     '''
        ...      a description with a leading space
        ...
        ...     Example:
        ...         >>> foobar
        ...     ''')
        >>> groups = split_google_docblocks(docstr)
        >>> print('groups = {!r}'.format(groups))

    Example:
        >>> from xdoctest.docstr.docscrape_google import *  # NOQA
        >>> from xdoctest import utils
        >>> docstr = utils.codeblock(
        ...     '''
        ...     Example:
        ...         >>> foobar
        ...     ''')
        >>> # Check that line offsets are valid if the first line is not blank
        >>> groups = split_google_docblocks(docstr)
        >>> offset = groups[0][1][1]
        >>> print('offset = {!r}'.format(offset))
        >>> assert offset == 0
        >>> # Check that line offsets are valid if the first line is blank
        >>> groups = split_google_docblocks(chr(10) + docstr)
        >>> offset = groups[0][1][1]
        >>> print('offset = {!r}'.format(offset))
        >>> assert offset == 1
    """
    if not isinstance(docstr, str):
        raise TypeError('Input docstr must be a string. Got {} instead'.format(
            type(docstr)))

    def get_indentation(line_):
        """ returns number of preceding spaces """
        return len(line_) - len(line_.lstrip())

    # Parse out initial documentation lines
    # Then parse out the blocked lines.
    docstr = ensure_unicode(docstr)

    docstr = textwrap.dedent(docstr)
    docstr_lines = docstr.split('\n')
    line_indent = [get_indentation(line) for line in docstr_lines]
    line_len = [len(line) for line in docstr_lines]

    # The first line may not have the correct indentation if it starts
    # right after the triple quotes. Adjust it in this case to ensure that
    # base indent is always 0
    adjusted = False
    is_nonzero = [len_ > 0 for len_ in line_len]
    if len(line_indent) >= 2:
        if line_len[0] != 0:
            indents = [x for x, f in zip(line_indent, is_nonzero) if f]
            if len(indents) >= 2:
                indent_adjust = min(indents[1:])
                line_indent[0] += indent_adjust
                line_len[0] += indent_adjust
                docstr_lines[0] = (' ' * indent_adjust) + docstr_lines[0]
                adjusted = True
    if adjusted:
        # Redo prepreocessing, but this time on a rectified input
        docstr = textwrap.dedent('\n'.join(docstr_lines))
        docstr_lines = docstr.split('\n')
        line_indent = [get_indentation(line) for line in docstr_lines]
        line_len = [len(line) for line in docstr_lines]

    indents = [x for x, f in zip(line_indent, is_nonzero) if f]
    if False and len(indents) >= 1:
        if indents[0] != 0:
            # debug info
            print('INDENTATION ERROR IN PARSING DOCSTRING')
            print('CHECK TO MAKE SURE YOU USED A RAW STRING IF YOU USE "\\n"')
            # TODO: Report this error with line number and file information
            print('Docstring:')
            print('----------')
            print(docstr)
            print('----------')
            raise exceptions.MalformedDocstr('malformed google docstr')

    base_indent = 0
    # We will group lines by their indentation.
    # Rectify empty lines by giving them their parent's indentation.
    true_indent = []
    prev_indent = None
    for indent_, len_ in zip(line_indent, line_len):
        if len_ == 0:
            # Empty lines take on their parents indentation
            indent_ = prev_indent
        true_indent.append(indent_)
        prev_indent = indent_

    # List of google style tags grouped by alias
    tag_groups = [
        ['Args', 'Arguments', 'Parameters', 'Other Parameters'],
        ['Kwargs', 'Keyword Args', 'Keyword Arguments'],
        ['Warns', 'Warning', 'Warnings'],
        ['Returns', 'Return'],
        ['Example', 'Examples'],
        ['Doctest'],
        ['Note', 'Notes'],
        ['Yields', 'Yield'],
        ['Attributes'],
        ['Methods'],
        ['Raises'],
        ['References'],
        ['See Also'],
        ['Todo'],
    ]
    # Map aliased tags to a canonical name (the first item in the group).
    tag_aliases = dict([(item, group[0]) for group in tag_groups for item in group])
    # Allow for single or double colon (support for pytorch)
    tag_pattern = '^' + '(' + '|'.join(tag_aliases.keys()) + ') *::? *$'

    # Label lines by their group-id
    group_id = 0
    prev_indent = 0
    group_list = []
    in_tag = False
    for line_num, (line, indent_) in enumerate(zip(docstr_lines, true_indent)):
        if re.match(tag_pattern, line):
            # Check if we can look ahead
            if line_num + 1 < len(docstr_lines):
                # A tag is only valid if its next line is properly indented,
                # empty, or is a tag itself.
                indent_increase = true_indent[line_num + 1] > base_indent
                indent_zero = line_len[line_num + 1] == 0
                matches_tag = re.match(tag_pattern, docstr_lines[line_num + 1])
                if (indent_increase or indent_zero or matches_tag):
                    group_id += 1
                    in_tag = True
            else:
                group_id += 1
                in_tag = True
        # If the indentation goes back to the base, then we have left the tag
        elif in_tag and indent_ != prev_indent and indent_ == base_indent:
            group_id += 1
            in_tag = False
        group_list.append(group_id)
        prev_indent = indent_

    assert len(docstr_lines) == len(group_list)

    # Group docstr lines by group list
    groups_ = collections.defaultdict(list)
    for groupid, line in zip(group_list, docstr_lines):
        groups_[groupid].append(line)

    groups = []
    line_offset = 0
    for k, lines in groups_.items():
        if len(lines) == 0 or (len(lines) == 1 and len(lines[0]) == 0):
            line_offset += len(lines)
            continue
        elif len(lines) >= 1 and re.match(tag_pattern, lines[0]):
            # An encoded google sub-block
            key = lines[0].strip().rstrip(':')
            val = lines[1:]
            subblock = textwrap.dedent('\n'.join(val))
        else:
            # A top level text documentation block
            key = '__DOC__'
            val = lines[:]
            subblock = '\n'.join(val)

        key = tag_aliases.get(key, key)
        block = DocBlock(subblock, line_offset)
        groups.append((key, block))
        line_offset += len(lines)
    return groups


def parse_google_args(docstr):
    r"""
    Generates dictionaries of argument hints based on a google docstring

    Args:
        docstr (str): a google-style docstring

    Yields:
        Dict[str, str]: dictionaries of parameter hints

    Example:
        >>> docstr = parse_google_args.__doc__
        >>> argdict_list = list(parse_google_args(docstr))
        >>> print([sorted(d.items()) for d in argdict_list])
        [[('desc', 'a google-style docstring'), ('name', 'docstr'), ('type', 'str')]]
    """
    blocks = split_google_docblocks(docstr)
    for key, block in blocks:
        lines = block[0]
        if key == 'Args':
            for argdict in parse_google_argblock(lines):
                yield argdict


def parse_google_returns(docstr, return_annot=None):
    r"""
    Generates dictionaries of possible return hints based on a google docstring

    Args:
        docstr (str): a google-style docstring

        return_annot (str | None):
            the return type annotation (if one exists)

    Yields:
        Dict[str, str]: dictionaries of return value hints

    Example:
        >>> docstr = parse_google_returns.__doc__
        >>> retdict_list = list(parse_google_returns(docstr))
        >>> print([sorted(d.items()) for d in retdict_list])
        [[('desc', 'dictionaries of return value hints'), ('type', 'Dict[str, str]')]]

    Example:
        >>> docstr = split_google_docblocks.__doc__
        >>> retdict_list = list(parse_google_returns(docstr))
        >>> print([sorted(d.items())[1] for d in retdict_list])
        [('type', 'List[Tuple[str, DocBlock]]')]
    """
    blocks = split_google_docblocks(docstr)
    for key, block in blocks:
        lines = block[0]
        if key == 'Returns':
            for retdict in parse_google_retblock(lines, return_annot):
                yield retdict
        if key == 'Yields':
            for retdict in parse_google_retblock(lines, return_annot):
                yield retdict


def parse_google_retblock(lines, return_annot=None):
    r"""
    Parse information out of a returns or yields block.

    A returns or yeids block should be formatted as one or more
    ``'{type}:{description}'`` strings. The description can occupy multiple
    lines, but the indentation should increase.

    Args:
        lines (str):
            unindented lines from a Returns or Yields section

        return_annot (str | None):
            the return type annotation (if one exists)

    Yields:
        Dict[str, str]: each dict specifies the return type and its description

    Example:
        >>> # Test various ways that retlines can be written
        >>> assert len(list(parse_google_retblock('list: a desc'))) == 1
        >>> # ---
        >>> hints = list(parse_google_retblock('\n'.join([
        ...     'entire line can be desc',
        ...     ' ',
        ...     ' if a return type annotation is given',
        ... ]), return_annot='int'))
        >>> assert len(hints) == 1
        >>> # ---
        >>> hints = list(parse_google_retblock('\n'.join([
        ...     'bool: a description',
        ...     ' with a newline',
        ... ])))
        >>> assert len(hints) == 1
        >>> # ---
        >>> hints = list(parse_google_retblock('\n'.join([
        ...     'int or bool: a description',
        ...     ' ',
        ...     ' with a separated newline',
        ...     ' ',
        ... ])))
        >>> assert len(hints) == 1
        >>> # ---
        >>> hints = list(parse_google_retblock('\n'.join([
        ...     # Multiple types can be specified
        ...     'threading.Thread: a description',
        ...     '(int, str): a tuple of int and str',
        ...     'tuple: a tuple of int and str',
        ...     'Tuple[int, str]: a tuple of int and str',
        ... ])))
        >>> assert len(hints) == 4
        >>> # ---
        >>> # If the colon is not specified nothing will be parsed
        >>> # according to the "official" spec, but lets try and do it anyway
        >>> hints = list(parse_google_retblock('\n'.join([
        ...     'list',
        ...     'Tuple[int, str]',
        ... ])))
        >>> assert len(hints) == 2
        >>> assert len(list(parse_google_retblock('no type, just desc'))) == 1
        ...
    """
    if return_annot is not None:
        # If the function has a return type annotation then the return block
        # should only be interpreted as a description. The formatting of the
        # lines is not modified in this case.
        retdict = {'type': return_annot, 'desc': lines}
        yield retdict
    else:
        # Otherwise, this examines each line without any extra indentation (wrt
        # the returns block) splits each line using a colon, and interprets
        # anything to the left of the colon as the type hint. The rest of the
        # parts are the description. Extra whitespace is removed from the
        # descriptions.
        def finalize(retdict):
            final_desc = ' '.join([p for p in retdict['desc'] if p])
            retdict['desc'] = final_desc
            return retdict
        retdict = None
        noindent_pat = re.compile(r'^[^\s]')
        for line in lines.split('\n'):
            # Lines without indentation should declare new type hints
            if noindent_pat.match(line):
                if retdict is not None:
                    # Finalize and return any previously constructed type hint
                    yield finalize(retdict)
                    retdict = None
                # FIXME:
                # This doesn't quite work if ":" is part of the type
                # definition.  Not sure if it can be. Needs better parsing
                # to ensure the ":" is actually the separator between
                # type and desc
                if ':' in line:
                    parts = line.split(':')
                    retdict = {
                        'type': parts[0].strip(),
                        'desc': [':'.join(parts[1:]).strip()],
                    }
                else:
                    # warning (malformatted google docstring) We should support
                    # the case where they just specify the type and no
                    # description.
                    USE_TYPE_HACK = 1
                    if USE_TYPE_HACK:
                        import ast
                        try:
                            ast.parse(line.strip())
                        except Exception:
                            # Not parseable, assume this is a description.
                            retdict = {
                                'type': None,
                                'desc': [line.strip()],
                            }
                        else:
                            # Parseable, assume this is a type
                            retdict = {
                                'type': line.strip(),
                                'desc': [],
                            }
            else:
                # Lines with indentation should extend previous descriptions.
                if retdict is not None:
                    retdict['desc'].append(line.strip())
        if retdict is not None:
            yield finalize(retdict)


def parse_google_argblock(lines, clean_desc=True):
    r"""
    Parse out individual items from google-style args blocks.

    Args:
        lines (str): the unindented lines from an Args docstring section

        clean_desc (bool):
            if True, will strip the description of newlines and indents.
            Defaults to True.

    Yields:
        Dict[str, str | None]:
            A dictionary containing keys, "name", "type", and "desc"
            corresponding to an argument in the Args block.

    Example:
        >>> # Test various ways that arglines can be written
        >>> line_list = [
        ...     '',
        ...     'foo1 (int): a description',
        ...     'foo2: a description\n    with a newline',
        ...     'foo3 (int or str): a description',
        ...     'foo4 (int or threading.Thread): a description',
        ...     #
        ...     # this is sphynx-like typing style
        ...     'param1 (:obj:`str`, optional): ',
        ...     'param2 (:obj:`list` of :obj:`str`):',
        ...     #
        ...     # the Type[type] syntax is defined by the python typeing module
        ...     'attr1 (Optional[int]): Description of `attr1`.',
        ...     'attr2 (List[str]): Description of `attr2`.',
        ...     'attr3 (Dict[str, str]): Description of `attr3`.',
        ...     '*args : variable positional args description',
        ...     '**kwargs : keyword arguments description',
        ...     'malformed and unparseable',
        ...     'param_no_desc1',  # todo: this should be parseable
        ...     'param_no_desc2:',
        ...     'param_no_desc3 ()',  # todo: this should be parseable
        ...     'param_no_desc4 ():',
        ...     'param_no_desc5 (str)',  # todo: this should be parseable
        ...     'param_no_desc6 (str):',
        ... ]
        >>> lines = '\n'.join(line_list)
        >>> argdict_list = list(parse_google_argblock(lines))
        >>> # All lines except the first should be accepted
        >>> assert len(argdict_list) == len(line_list) - 5
        >>> assert argdict_list[1]['desc'] == 'a description with a newline'
    """
    def named(key, pattern):
        return '(?P<{}>{})'.format(key, pattern)
    def optional(pattern):
        return '({})?'.format(pattern)
    def positive_lookahead(pattern):
        return '(?={})'.format(pattern)
    def regex_or(patterns):
        return '({})'.format('|'.join(patterns))
    whitespace = r'\s*'
    endofstr = r'\Z'

    # Define characters that can be part of variable / type names
    # Note: a variable name might be prefixed with 0, 1, or 2, `*` to indicate
    # *args or **kwargs
    varname = named('name', r'\*?\*?[A-Za-z_][A-Za-z0-9_]*')
    typename = named('type', '[^)]*?')
    argdesc = named('desc', '.*?')
    # Types are optional, and must be enclosed in parens
    optional_type = optional(whitespace.join([r'\(', typename, r'\)']))
    # Each arg hint must defined a on newline without any indentation
    argdef = whitespace.join([varname, optional_type, ':'])
    # the description is everything after the colon until either the next line
    # without any indentation or the end of the string
    end_desc = regex_or(['^' + positive_lookahead(r'[^\s]'), endofstr])

    flags = re.MULTILINE | re.DOTALL
    argline_pat = re.compile('^' + argdef + argdesc + end_desc, flags=flags)

    for match in argline_pat.finditer(lines):
        argdict = match.groupdict()
        # Clean description
        if clean_desc:
            desc_lines = [p.strip() for p in argdict['desc'].split('\n')]
            argdict['desc'] = ' '.join([p for p in desc_lines if p])

        yield argdict

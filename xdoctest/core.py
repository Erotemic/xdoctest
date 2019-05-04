# -*- coding: utf-8 -*-
"""
Core methods used by xdoctest runner and plugin code to statically extract
doctests from a module or package.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import textwrap
import warnings
import six
import itertools as it
from os.path import exists
from fnmatch import fnmatch
from xdoctest import dynamic_analysis as dynamic
from xdoctest import static_analysis as static
from xdoctest import parser
from xdoctest import exceptions
from xdoctest import doctest_example
from xdoctest import utils  # NOQA
from xdoctest.docstr import docscrape_google


DEBUG = False


DOCTEST_STYLES = [
    'freeform',
    'google',
    'auto',
    # 'numpy',  # TODO
]


def parse_freeform_docstr_examples(docstr, callname=None, modpath=None,
                                   lineno=1, fpath=None, asone=True):
    r"""
    Finds free-form doctests in a docstring. This is similar to the original
    doctests because these tests do not requires a google/numpy style header.

    Some care is taken to avoid enabling tests that look like disabled google
    doctests or scripts.

    Args:
        asone (bool): if False doctests are broken into multiple examples
           based on spacing. (default True)

        lineno (int): the line number (starting from 1) of the docstring.
            i.e. if you were to go to this line number in the source file
            the starting quotes of the docstr would be on this line.

    Raises:
        xdoctest.exceptions.DoctestParseError: if an error occurs in parsing

    CommandLine:
        python -m xdoctest.core parse_freeform_docstr_examples

    Example:
        >>> from xdoctest import core
        >>> from xdoctest import utils
        >>> docstr = utils.codeblock(
        >>>     '''
        >>>     freeform
        >>>     >>> doctest
        >>>     >>> hasmultilines
        >>>     whoppie
        >>>     >>> 'butthis is the same doctest'
        >>>
        >>>     >>> secondone
        >>>
        >>>     Script:
        >>>         >>> 'special case, dont parse me'
        >>>
        >>>     DisableDoctest:
        >>>         >>> 'special case, dont parse me'
        >>>         want
        >>>
        >>>     AnythingElse:
        >>>         >>> 'general case, parse me'
        >>>        want
        >>>     ''')
        >>> examples = list(parse_freeform_docstr_examples(docstr, asone=True))
        >>> assert len(examples) == 1
        >>> examples = list(parse_freeform_docstr_examples(docstr, asone=False))
        >>> assert len(examples) == 3
    """

    def doctest_from_parts(parts, num, curr_offset):
        # FIXME: this will cause line numbers to become misaligned
        nested = [
            p.orig_lines
            if p.want is None else
            p.orig_lines + p.want.splitlines()
            for p in parts
        ]
        docsrc = '\n'.join(list(it.chain.from_iterable(nested)))
        docsrc = textwrap.dedent(docsrc)

        example = doctest_example.DocTest(docsrc, modpath=modpath,
                                          callname=callname, num=num,
                                          lineno=lineno + curr_offset,
                                          fpath=fpath)
        # rebase the offsets relative to the test lineno (ie start at 0)
        unoffset = parts[0].line_offset
        for p in parts:
            p.line_offset -= unoffset
        # We've already parsed the parts, so we dont need to do it again
        example._parts = parts
        return example

    if DEBUG:
        print('Parsing docstring for callname={} in modpath={}'.format(
            callname, modpath))

    respect_google_headers = True
    if respect_google_headers:  # pragma: nobranch
        # TODO: make configurable
        # When in freeform mode we still try to respect google doctest patterns
        # that prevent a test from being run.
        special_skip_patterns = [
            'DisableDoctest:',
            'DisableExample:',
            'SkipDoctest:',
            'Ignore:',
            'Script:',
            'Benchmark:',
            'Sympy:',
        ]
    else:
        special_skip_patterns = []  # nocover
    special_skip_patterns_ = tuple([
        p.lower() for p in special_skip_patterns
    ])

    def _start_ignoring(prev):
        return (special_skip_patterns_ and
                isinstance(prev, six.string_types) and
                prev.strip().lower().endswith(special_skip_patterns_))

    # parse into doctest and plaintext parts
    info = dict(callname=callname, modpath=modpath, lineno=lineno, fpath=fpath)
    all_parts = list(parser.DoctestParser().parse(docstr, info))

    curr_parts = []
    curr_offset = 0
    num = 0
    prev_part = None
    ignoring = False

    for part in all_parts:
        if isinstance(part, six.string_types):
            # Part is a plaintext
            if asone:
                # Lump all doctest parts into one example
                if not curr_parts:
                    curr_offset += part.count('\n') + 1
            else:  # nocover
                if curr_parts:
                    # Group the current parts into a single doctest
                    example = doctest_from_parts(curr_parts, num, curr_offset)
                    yield example
                    # Initialize empty parts for a new doctest
                    curr_offset += sum(p.n_lines for p in curr_parts)
                    num += 1
                    curr_parts = []
                curr_offset += part.count('\n') + 1
            # stop ignoring
            ignoring = False
        else:
            # If the previous part was text-based, and matches a special skip
            # ignore pattern then ignore all tests until a new doctest block
            # begins. (different doctest blocks are separated by plaintext)
            if ignoring or _start_ignoring(prev_part):
                ignoring = True
                if asone:
                    if not curr_parts:
                        curr_offset += part.n_lines
                else:
                    curr_offset += part.n_lines
            else:
                # Append part to the current parts
                curr_parts.append(part)
        prev_part = part
    if curr_parts:
        # Group remaining parts into the final doctest
        example = doctest_from_parts(curr_parts, num, curr_offset)
        yield example


def parse_google_docstr_examples(docstr, callname=None, modpath=None, lineno=1,
                                 fpath=None, eager_parse=True):
    """
    Parses Google-style doctests from a docstr and generates example objects

    Args:
        lineno (int): the line number (starting from 1) of the docstring.
            i.e. if you were to go to this line number in the source file
            the starting quotes of the docstr would be on this line.

    Raises:
        xdoctest.exceptions.MalformedDocstr: if an error occurs in finding google blocks
        xdoctest.exceptions.DoctestParseError: if an error occurs in parsing
    """
    try:
        blocks = docscrape_google.split_google_docblocks(docstr)
    except exceptions.MalformedDocstr:
        print('ERROR PARSING {} GOOGLE BLOCKS IN {} ON line {}'.format(
            callname, modpath, lineno))
        print('Did you forget to make a docstr with newlines raw?')
        raise
    example_blocks = []
    example_tags = ('Example', 'Doctest', 'Script', 'Benchmark')
    for type, block in blocks:
        if type.startswith(example_tags):
            example_blocks.append((type, block))
    for num, (type, (docsrc, offset)) in enumerate(example_blocks):
        # Add one because offset indicates the position of the block-label
        # and the body of the block always starts on the next line.
        label_lineno = lineno + offset
        body_lineno = label_lineno + 1
        example = doctest_example.DocTest(docsrc, modpath, callname, num,
                                          lineno=body_lineno, fpath=fpath,
                                          block_type=type)
        if eager_parse:
            # parse on the fly to be consistent with freeform?
            example._parse()
        yield example


def parse_auto_docstr_examples(docstr, *args, **kwargs):
    """
    First try to parse google style, but if no tests are found use freeform
    style.
    """
    if DEBUG:
        print('Automatic style is trying google parsing')

    n_found = 0
    try:
        for example in parse_google_docstr_examples(docstr, *args, **kwargs):
            n_found += 1
            yield example
    except Exception:
        if n_found > 0:
            raise

    # no google style tests were found, parse in freeform
    if n_found == 0:
        if DEBUG:
            print('Automatic style is trying freeform parsing')
        for example in parse_freeform_docstr_examples(docstr, *args, **kwargs):
            yield example


def parse_docstr_examples(docstr, callname=None, modpath=None, lineno=1,
                          style='auto', fpath=None, parser_kw={}):
    """
    Parses doctests from a docstr and generates example objects.
    The style influences which tests are found.

    Args:
        docstr (str): a previously extracted docstring

        callname (str): function or class name or class and method name

        modpath (PathLike): original module the docstring is from

        lineno (int): the line number (starting from 1) of the docstring.
            i.e. if you were to go to this line number in the source file
            the starting quotes of the docstr would be on this line.

        style (str): expected doctest style (e.g. google, freeform, auto)

        fpath (PathLike): the file that the docstring is from
            (if the file was not a module, needed for backwards compatibility)

        parser_kw (dict): passed to the parser

    CommandLine:
        python -m xdoctest.core parse_docstr_examples

    Example:
        >>> from xdoctest.core import *
        >>> from xdoctest import utils
        >>> docstr = utils.codeblock(
        ...    '''
        ...    >>> 1 + 1  # xdoctest: +SKIP
        ...    2
        ...    >>> 2 + 2
        ...    4
        ...    ''')
        >>> examples = list(parse_docstr_examples(docstr, 'name', fpath='foo.txt', style='freeform'))
        >>> print(len(examples))
        1
        >>> examples = list(parse_docstr_examples(docstr, fpath='foo.txt'))
    """
    if DEBUG:
        print('Parsing docstring examples for '
              'callname={} in modpath={}'.format(callname, modpath))
    if style == 'freeform':
        parser = parse_freeform_docstr_examples
    elif style == 'google':
        parser = parse_google_docstr_examples
    elif style == 'auto':
        parser = parse_auto_docstr_examples
    # TODO:
    # elif style == 'numpy':
    #     parser = parse_numpy_docstr_examples
    else:
        raise KeyError('Unknown style={}. Valid styles are {}'.format(
            style, DOCTEST_STYLES))

    if DEBUG:
        print('parser = {!r}'.format(parser))

    n_parsed = 0
    try:
        for example in parser(docstr, callname=callname, modpath=modpath,
                              fpath=fpath, lineno=lineno, **parser_kw):
            n_parsed += 1
            yield example
    except Exception as ex:
        if DEBUG:
            print('Caught an error when parsing')
        msg = ('Cannot scrape callname={} in modpath={} line={}.\n'
               'Caused by: {}\n')
        # raise
        msg = msg.format(callname, modpath, lineno, repr(ex))
        if isinstance(ex, exceptions.DoctestParseError):
            # TODO: Can we print a nicer syntax error here?

            msg += '{}\n'.format(ex.string)
            msg += 'Original Error: {}\n'.format(repr(ex.orig_ex))

            if isinstance(ex.orig_ex, SyntaxError):
                extra_help = ''
                if ex.orig_ex.text:
                    extra_help += utils.ensure_unicode(ex.orig_ex.text)
                if ex.orig_ex.offset is not None:
                    extra_help += ' ' * (ex.orig_ex.offset - 1) + '^'
                if extra_help:
                    msg += '\n' + extra_help

        # Always warn when something bad is happening.
        # However, dont error if the docstr simply has bad syntax
        print('msg = {}'.format(msg))
        warnings.warn(msg)
        if isinstance(ex, exceptions.MalformedDocstr):
            pass
        elif isinstance(ex, exceptions.DoctestParseError):
            pass
        else:
            raise
    if DEBUG:
        print('Finished parsing {} examples'.format(n_parsed))


def _rectify_to_modpath(modpath_or_name):
    """ if modpath_or_name is a name, statically converts it to a path """
    modpath = static.modname_to_modpath(modpath_or_name)
    if modpath is None:
        if six.PY2:
            if modpath_or_name.endswith('.pyc'):
                modpath_or_name = modpath_or_name[:-1]
        if exists(modpath_or_name):
            modpath = modpath_or_name
        else:
            raise ValueError('Cannot find module={}'.format(modpath_or_name))
    return modpath


def package_calldefs(modpath_or_name, exclude=[], ignore_syntax_errors=True):
    """
    Statically generates all callable definitions in a module or package

    Args:
        modpath_or_name (str): path to or name of the module to be tested
        exclude (List[str]): glob-patterns of file names to exclude
        ignore_syntax_errors (bool): if False raise an error when syntax errors
            occur in a doctest (default True)

    Example:
        >>> modpath_or_name = 'xdoctest.core'
        >>> testables = list(package_calldefs(modpath_or_name))
        >>> assert len(testables) == 1
        >>> calldefs, modpath = testables[0]
        >>> assert static.modpath_to_modname(modpath) == modpath_or_name
        >>> assert 'package_calldefs' in calldefs
    """
    pkgpath = _rectify_to_modpath(modpath_or_name)

    modpaths = static.package_modpaths(pkgpath, with_pkg=True, with_libs=True)
    modpaths = list(modpaths)
    for modpath in modpaths:
        modname = static.modpath_to_modname(modpath)
        if any(fnmatch(modname, pat) for pat in exclude):
            continue
        if not exists(modpath):
            warnings.warn(
                'Module {} does not exist. '
                'Is it an old pyc file?'.format(modname))
            continue

        FORCE_DYNAMIC = '--xdoc-force-dynamic' in sys.argv
        # if false just skip extension modules
        # ALLOW_DYNAMIC = '--no-xdoc-dynamic' not in sys.argv
        ALLOW_DYNAMIC = '--allow-xdoc-dynamic' in sys.argv

        needs_dynamic = False

        if FORCE_DYNAMIC:
            # Force dynamic parsing for everything
            do_dynamic = True
        else:
            # Some modules can only be parsed dynamically
            needs_dynamic = modpath.endswith(static._platform_pylib_exts())
            do_dynamic = needs_dynamic and ALLOW_DYNAMIC

        if do_dynamic:
            try:
                calldefs = dynamic.parse_dynamic_calldefs(modpath)
            except ImportError as ex:
                # Some modules are just c modules
                msg = 'Cannot dynamically parse module={} at path={}.\nCaused by: {!r} {}'
                msg = msg.format(modname, modpath, type(ex), ex)
                warnings.warn(msg)
            except Exception as ex:
                msg = 'Cannot dynamically parse module={} at path={}.\nCaused by: {!r} {}'
                msg = msg.format(modname, modpath, type(ex), ex)
                warnings.warn(msg)
                raise
            else:
                yield calldefs, modpath
        else:
            if needs_dynamic:
                continue

            try:
                calldefs = static.parse_calldefs(fpath=modpath)
            except SyntaxError as ex:
                # Handle error due to the actual code containing errors
                msg = 'Cannot parse module={} at path={}.\nCaused by: {}'
                msg = msg.format(modname, modpath, ex)
                if ignore_syntax_errors:
                    warnings.warn(msg)  # real code or docstr contained errors
                    continue
                else:
                    raise SyntaxError(msg)
            else:
                yield calldefs, modpath


def parse_doctestables(modpath_or_name, exclude=[], style='auto',
                       ignore_syntax_errors=True, parser_kw={}):
    """
    Parses all doctests within top-level callables of a module and generates
    example objects.  The style influences which tests are found.

    Args:
        modpath_or_name (str|PathLike): path or name of a module
        exclude (List[str]): glob-patterns of file names to exclude
        style (str): expected doctest style (e.g. google, freeform, auto)
        ignore_syntax_errors (bool): if False raise an error when syntax errors
            occur in a doctest (default True)
        parser_kw: extra args passed to the parser

    Yields:
        xdoctest.doctest_example.DocTest : parsed doctest example objects

    CommandLine:
        python -m xdoctest.core parse_doctestables

    Example:
        >>> modpath_or_name = 'xdoctest.core'
        >>> testables = list(parse_doctestables(modpath_or_name))
        >>> this_example = None
        >>> for example in testables:
        >>>     # print(example)
        >>>     if example.callname == 'parse_doctestables':
        >>>         this_example = example
        >>> assert this_example is not None
        >>> assert this_example.callname == 'parse_doctestables'

    Example:
        >>> from xdoctest import utils
        >>> docstr = utils.codeblock(
        ...    '''
        ...    >>> 1 + 1  # xdoctest: +SKIP
        ...    2
        ...    >>> 2 + 2
        ...    4
        ...    ''')
        >>> temp = utils.TempDoctest(docstr, 'test_modfile')
        >>> modpath = temp.modpath
        >>> examples = list(parse_doctestables(modpath, style='freeform'))
        >>> print(len(examples))
        1
    """

    if style not in DOCTEST_STYLES:
        raise KeyError('Unknown style={}. Valid styles are {}'.format(
            style, DOCTEST_STYLES))

    # Statically parse modules and their doctestable callables in a package
    for calldefs, modpath in package_calldefs(modpath_or_name, exclude,
                                              ignore_syntax_errors):
        for callname, calldef in calldefs.items():
            docstr = calldef.docstr
            if calldef.docstr is not None:
                lineno = calldef.doclineno
                for example in parse_docstr_examples(docstr, callname=callname,
                                                     modpath=modpath,
                                                     lineno=lineno,
                                                     style=style,
                                                     parser_kw=parser_kw):
                    yield example


if __name__ == '__main__':
    """
    CommandLine:
        python -m xdoctest.core all
    """
    import xdoctest as xdoc
    xdoc.doctest_module()

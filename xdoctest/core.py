# -*- coding: utf-8 -*-
"""
Core methods used by xdoctest runner and plugin code to statically extract
doctests from a module or package.


The following is a glossary of terms and jargon used in this repo.

* callname - the name of a callable function, method, class etc... e.g.
  ``myfunc``, ``MyClass``, or ``MyClass.some_method``.

* got / want - a test that produces stdout or a value to check. Whatever is
  produced is what you "got" and whatever is expected is what you "want".
  See :mod:`xdoctest.checker` for more details.

* directives - special in-doctest comments that change the behavior of the
  doctests at runtime. See :mod:`xdoctest.directive` for more details.

* the three cheverons (``>>> ``) - this is the standard prefix for a doctest,
  also referred to as a PS1 line in the parser.

* TODO - complete this list.

"""
from __future__ import absolute_import, division, print_function, unicode_literals
import sys
import textwrap
import warnings
import six
import itertools as it
import types
from os.path import exists
from fnmatch import fnmatch
from xdoctest import dynamic_analysis
from xdoctest import static_analysis
from xdoctest import parser
from xdoctest import exceptions
from xdoctest import doctest_example
from xdoctest import utils
from xdoctest.docstr import docscrape_google
from xdoctest.utils import util_import


DEBUG = '--debug' in sys.argv


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
        docstr (str): an extracted docstring

        callname (str, default=None):
            the name of the callable (e.g. function, class, or method)
            that this docstring belongs to.

        modpath (str | PathLike, default=None):
            original module the docstring is from

        lineno (int, default=1):
            the line number (starting from 1) of the docstring.  i.e. if you
            were to go to this line number in the source file the starting
            quotes of the docstr would be on this line.

        fpath (str | PathLike, default=None):
            the file that the docstring is from (if the file was not a module,
            needed for backwards compatibility)

        asone (bool, default=True):
            if False doctests are broken into multiple examples based on
            spacing, otherwise they are executed as a single unit.

    Yields:
        xdoctest.doctest_example.DocTest : doctest object

    Raises:
        xdoctest.exceptions.DoctestParseError: if an error occurs in parsing

    CommandLine:
        python -m xdoctest.core parse_freeform_docstr_examples

    Example:
        >>> # TODO: move this to unit tests and make the doctest simpler
        >>> from xdoctest import core
        >>> from xdoctest import utils
        >>> docstr = utils.codeblock(
        >>>     '''
        >>>     freeform
        >>>     >>> doctest
        >>>     >>> hasmultilines
        >>>     whoppie
        >>>     >>> 'but this is the same doctest'
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
        docstr (str): an extracted docstring

        callname (str, default=None):
            the name of the callable (e.g. function, class, or method)
            that this docstring belongs to.

        modpath (str | PathLike, default=None):
            original module the docstring is from

        lineno (int, default=1):
            the line number (starting from 1) of the docstring.  i.e. if you
            were to go to this line number in the source file the starting
            quotes of the docstr would be on this line.

        fpath (str | PathLike, default=None):
            the file that the docstring is from (if the file was not a module,
            needed for backwards compatibility)

        eager_parse (bool, default=True):
            if True eagerly evaluate the parser inside the google example
            blocks

    Yields:
        xdoctest.doctest_example.DocTest : doctest object

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

        callname (str, default=None):
            the name of the callable (e.g. function, class, or method)
            that this docstring belongs to.

        modpath (str | PathLike, default=None):
            original module the docstring is from

        lineno (int, default=1):
            the line number (starting from 1) of the docstring.  i.e. if you
            were to go to this line number in the source file the starting
            quotes of the docstr would be on this line.

        style (str, default='auto'): expected doctest style, which can
            be "google", "freeform", or "auto".

        fpath (str | PathLike, default=None):
            the file that the docstring is from (if the file was not a module,
            needed for backwards compatibility)

        parser_kw (dict, default={}): passed to the parser

    Yields:
        xdoctest.doctest_example.DocTest : parsed example

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
    if isinstance(modpath_or_name, types.ModuleType):
        raise TypeError('Expected a static module but got a dynamic one')
    modpath = util_import.modname_to_modpath(modpath_or_name)
    if modpath is None:
        if six.PY2:
            if modpath_or_name.endswith('.pyc'):
                modpath_or_name = modpath_or_name[:-1]
        if exists(modpath_or_name):
            modpath = modpath_or_name
        else:
            raise ValueError('Cannot find module={}'.format(modpath_or_name))
    return modpath


def package_calldefs(pkg_identifier, exclude=[], ignore_syntax_errors=True,
                     analysis='auto'):
    """
    Statically generates all callable definitions in a module or package

    Args:
        pkg_identifier (str | Module): path to or name of the module to be
            tested (or the live module itself, which is not recommended)

        exclude (List[str]): glob-patterns of file names to exclude

        ignore_syntax_errors (bool, default=True):
            if False raise an error when syntax errors occur in a doctest

        analysis (str, default='auto'):
            if 'static', only static analysis is used to parse call
            definitions. If 'auto', uses dynamic analysis for compiled python
            extensions, but static analysis elsewhere, if 'dynamic', then
            dynamic analysis is used to parse all calldefs.

    Yields:
        Tuple[Dict[str, CallDefNode], str | Module] -
            * item[0]: the mapping of callnames-to-calldefs
            * item[1]: the path to the file containing the doctest
              (usually a module) or the module itself

    Example:
        >>> pkg_identifier = 'xdoctest.core'
        >>> testables = list(package_calldefs(pkg_identifier))
        >>> assert len(testables) == 1
        >>> calldefs, modpath = testables[0]
        >>> assert util_import.modpath_to_modname(modpath) == pkg_identifier
        >>> assert 'package_calldefs' in calldefs
    """
    if isinstance(pkg_identifier, types.ModuleType):
        # Case where we are forced to use a live module
        identifiers = [pkg_identifier]
    else:
        pkgpath = _rectify_to_modpath(pkg_identifier)
        identifiers = list(static_analysis.package_modpaths(
            pkgpath, with_pkg=True, with_libs=True))

    for module_identifier in identifiers:
        if isinstance(module_identifier, six.string_types):
            modpath = module_identifier
            modname = util_import.modpath_to_modname(modpath)
            if any(fnmatch(modname, pat) for pat in exclude):
                continue
            if not exists(modpath):
                warnings.warn(
                    'Module {} does not exist. '
                    'Is it an old pyc file?'.format(modname))
                continue
        try:
            calldefs = parse_calldefs(module_identifier)
            if calldefs is not None:
                yield calldefs, module_identifier
        except SyntaxError as ex:
            # Handle error due to the actual code containing errors
            msg = 'Cannot parse module={}.\nCaused by: {}'
            msg = msg.format(module_identifier, ex)
            if ignore_syntax_errors:
                warnings.warn(msg)  # real code or docstr contained errors
            else:
                raise SyntaxError(msg)


def parse_calldefs(module_identifier, analysis='auto'):
    """
    Parse calldefs from a single module using either static or dynamic
    analysis.

    Args:
        module_identifier (str | Module): path to or name of the module to be
            tested (or the live module itself, which is not recommended)

        analysis (str, default='auto'):
            if 'static', only static analysis is used to parse call
            definitions. If 'auto', uses dynamic analysis for compiled python
            extensions, but static analysis elsewhere, if 'dynamic', then
            dynamic analysis is used to parse all calldefs.

    Returns:
        Dict[str, CallDefNode]: the mapping of callnames-to-calldefs within
          the module.
    """
    # backwards compatibility hacks
    if '--allow-xdoc-dynamic' in sys.argv:
        warnings.warn(
            '--allow-xdoc-dynamic is deprecated  and will be removed in '
            'the future use --analysis=auto instead', DeprecationWarning)
        analysis = 'auto'
    if '--xdoc-force-dynamic' in sys.argv:
        warnings.warn(
            '--xdoc-force-dynamic is deprecated and will be removed in '
            'the future use --analysis=dynamic instead', DeprecationWarning)
        analysis = 'dynamic'

    if isinstance(module_identifier, types.ModuleType):
        # identifier is a live module
        need_dynamic = True
    else:
        # identifier is a path to a module
        modpath = module_identifier
        # Certain files (notebooks and c-extensions) require dynamic analysis
        need_dynamic = modpath.endswith(
            static_analysis._platform_pylib_exts())
        if modpath.endswith('.ipynb'):
            need_dynamic = True

    if analysis == 'static':
        if need_dynamic:
            # Some modules can only be parsed dynamically
            raise Exception((
                'Static analysis required, but {} requires '
                'dynamic analysis').format(module_identifier))
        do_dynamic = False
    elif analysis == 'dynamic':
        do_dynamic = True
    elif analysis == 'auto':
        do_dynamic = need_dynamic
    else:
        raise KeyError(analysis)

    calldefs = None
    if do_dynamic:
        try:
            calldefs = dynamic_analysis.parse_dynamic_calldefs(module_identifier)
        except (ImportError, RuntimeError) as ex:
            # Some modules are just c modules
            msg = 'Cannot dynamically parse module={}.\nCaused by: {!r} {}'
            msg = msg.format(module_identifier, type(ex), ex)
            warnings.warn(msg)
        except Exception as ex:
            msg = 'Cannot dynamically parse module={}.\nCaused by: {!r} {}'
            msg = msg.format(module_identifier, type(ex), ex)
            warnings.warn(msg)
            raise
    else:
        calldefs = static_analysis.parse_static_calldefs(fpath=module_identifier)

    return calldefs


def parse_doctestables(module_identifier, exclude=[], style='auto',
                       ignore_syntax_errors=True, parser_kw={},
                       analysis='static'):
    """
    Parses all doctests within top-level callables of a module and generates
    example objects.  The style influences which tests are found.

    Args:
        module_identifier (str | PathLike | Module):
            path or name of a module or a module itself (we prefer a path)

        exclude (List[str]): glob-patterns of file names to exclude

        style (str): expected doctest style (e.g. google, freeform, auto)

        ignore_syntax_errors (bool, default=True):
            if False raise an error when syntax errors

        parser_kw: extra args passed to the parser

        analysis (str, default='static'):
            if 'static', only static analysis is used to parse call
            definitions. If 'auto', uses dynamic analysis for compiled python
            extensions, but static analysis elsewhere, if 'dynamic', then
            dynamic analysis is used to parse all calldefs.

    Yields:
        xdoctest.doctest_example.DocTest : parsed doctest example objects

    CommandLine:
        python -m xdoctest.core parse_doctestables

    Example:
        >>> module_identifier = 'xdoctest.core'
        >>> testables = list(parse_doctestables(module_identifier))
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
    for calldefs, modpath in package_calldefs(module_identifier, exclude,
                                              ignore_syntax_errors,
                                              analysis=analysis):
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

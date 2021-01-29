def argsort(indexable, key=None, reverse=False):
    """
    Returns the indices that would sort a indexable object.

    This is similar to :func:`numpy.argsort`, but it is written in pure python
    and works on both lists and dictionaries.

    Args:
        indexable (Iterable[B] | Mapping[A, B]): indexable to sort by

        key (Callable[[A], B], default=None):
            customizes the ordering of the indexable

        reverse (bool, default=False): if True returns in descending order

    Returns:
        List[int]: indices - list of indices such that sorts the indexable

    Example:
        >>> # argsort works on dicts by returning keys
        >>> dict_ = {'a': 3, 'b': 2, 'c': 100}
        >>> indices = argsort(dict_)
        >>> # argsort works on lists by returning indices
        >>> indexable = [100, 2, 432, 10]
        >>> indices = argsort(indexable)
        >>> # Can use iterators, but be careful. It exhausts them.
        >>> indexable = reversed(range(100))
        >>> indices = argsort(indexable)
        >>> assert indices[0] == 99
        >>> # Can use key just like sorted
        >>> indexable = [[0, 1, 2], [3, 4], [5]]
        >>> indices = argsort(indexable, key=len)
        >>> # Can use reverse just like sorted
        >>> indexable = [0, 2, 1]
        >>> indices = argsort(indexable, reverse=True)
    """
    try:
        from collections import abc as collections_abc
    except Exception:  # nocover
        import collections as collections_abc
    # Create an iterator of value/key pairs
    if isinstance(indexable, collections_abc.Mapping):
        vk_iter = ((v, k) for k, v in indexable.items())
    else:
        vk_iter = ((v, k) for k, v in enumerate(indexable))
    # Sort by values and extract the indices
    if key is None:
        indices = [k for v, k in sorted(vk_iter, reverse=reverse)]
    else:
        # If key is provided, call it using the value as input
        indices = [k for v, k in sorted(vk_iter, key=lambda vk: key(vk[0]),
                                        reverse=reverse)]
    return indices


def convert_file_docstrings(path_to_convert, dry=True):
    """
    path_to_convert = ub.expandpath('~/code/networkx/networkx/algorithms/isomorphism/_embeddinghelpers/balanced_sequence.py')
    """
    from xdoctest.core import package_calldefs
    pkg_calldefs = list(package_calldefs(path_to_convert))
    def recnone(val, default):
        return default if val is None else val

    for calldefs, modpath in pkg_calldefs:
        to_insert = []
        with open(modpath, 'r') as file:
            old_text = file.read()
        old_lines = old_text.split('\n')
        sortnames = argsort(calldefs, key=lambda node: recnone(node.doclineno, -1))
        for name in sortnames:
            node = calldefs[name]
            if node.docstr is not None:
                google_docstr = node.docstr
                numpy_docstr = google_to_numpy_docstr(google_docstr)
                body_lines = numpy_docstr.split('\n')
                start = node.doclineno
                stop = node.doclineno_end
                to_insert.append((start, stop, body_lines))

        to_insert = sorted(to_insert)[::-1]

        new_lines = old_lines.copy()
        for start, stop, body_lines in to_insert:
            old_middle = old_lines[start - 1:stop]
            print('old_middle = {}'.format(old_middle))
            print('start = {!r}'.format(start))
            startline = new_lines[start - 1]
            print('startline = {!r}'.format(startline))
            ssline = startline.strip(' ')
            sq = ssline[0]
            tq = sq * 3
            n_indent = len(startline) - len(ssline)
            indent = ' ' * n_indent
            print('n_indent = {!r}'.format(n_indent))
            body_lines = [indent + line for line in body_lines]
            body_lines = [indent + tq] + body_lines + [indent + tq]
            prefix = new_lines[: start - 1]
            suffix = new_lines[stop:]
            mid = body_lines
            new_lines = prefix + mid + suffix

        new_text = '\n'.join(new_lines)
        # print(new_text)
        if dry:
            import xdev
            print(xdev.misc.difftext(old_text, new_text, context_lines=10, colored=True))
            print('^^^ modpath = {!r}'.format(modpath))
        else:
            with open(modpath, 'w') as file:
                file.write(new_text)


def google_to_numpy_docstr(docstr):
    """
    Convert a google-style docstring to a numpy-style docstring

    Args:
        docstr (str): contents of ``func.__doc__`` for some ``func``, assumed
            to be in google-style.

    Returns:
        str: numpy style docstring
    """
    from xdoctest.utils.util_str import indent as indent_fn
    from xdoctest.docstr import docscrape_google
    docblocks = docscrape_google.split_google_docblocks(docstr)
    new_parts = []
    for key, block in docblocks:
        old_body, relpos = block
        new_key = key
        new_body = old_body

        if key == '__DOC__':
            new_key = None
            new_text = new_body
        elif key in {'Args'}:
            new_key = 'Parameters'
            arginfos = list(
                docscrape_google.parse_google_argblock(old_body))
            parts = []
            for info in arginfos:
                info['desc'] = indent_fn(info['desc'])
                p = '{name}: {type}\n{desc}'.format(**info)
                parts.append(p)
                parts.append('')
            new_body = '\n'.join(parts)
        if key in {'Returns', 'Yields'}:
            retinfos = list(
                docscrape_google.parse_google_retblock(old_body))
            parts = []
            for info in retinfos:
                info['desc'] = indent_fn(info['desc'])
                info['name'] = info.get('name', '')
                parts.append('{name}: {type}\n{desc}'.format(**info))
                parts.append('')
            new_body = '\n'.join(parts)

        if new_key is not None:
            new_text = '\n'.join(
                [new_key, '-' * len(new_key), new_body])

        if new_text.strip():
            new_parts.append(new_text)

    new_docstr = '\n'.join(new_parts)
    new_docstr = new_docstr.strip('\n')
    return new_docstr


def main():
    import scriptconfig as scfg
    class Config(scfg.Config):
        default = {
            'src': scfg.Value(None, help='path to file to convert'),
            'dry': scfg.Value(True, help='set to false to execute'),
        }
    config = Config(cmdline=True)
    path_to_convert = config['src']
    dry = config['dry']
    convert_file_docstrings(path_to_convert, dry=dry)


if __name__ == '__main__':
    """
    CommandLine:
        python -m xdoctest.docstr.convert_google_to_numpy --src ~/code/networkx/networkx/algorithms/isomorphism/_embeddinghelpers/balanced_sequence.py
    """
    main()

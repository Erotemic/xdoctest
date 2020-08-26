

def convert_file_docstrings(path_to_convert, dry=True):
    """
    path_to_convert = ub.expandpath('~/code/networkx/networkx/algorithms/isomorphism/_embeddinghelpers/balanced_sequence.py')
    """
    import ubelt as ub
    from xdoctest.core import package_calldefs
    pkg_calldefs = list(package_calldefs(path_to_convert))
    def recnone(val, default):
        return default if val is None else val

    for calldefs, modpath in pkg_calldefs:
        to_insert = []
        old_text = ub.readfrom(modpath)
        old_lines = old_text.split('\n')
        sortnames = ub.argsort(calldefs, key=lambda node: recnone(node.doclineno, -1))
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
            print('old_middle = {}'.format(ub.repr2(old_middle, nl=1)))
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
            ub.writeto(modpath, new_text, verbose=3)


def google_to_numpy_docstr(docstr):
    """
    Convert a google-style docstring to a numpy-style docstring

    Args:
        docstr (str): contents of ``func.__doc__`` for some ``func``, assumed
            to be in google-style.

    Returns:
        str: numpy style docstring
    """
    import ubelt as ub
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
                info['desc'] = ub.indent(info['desc'])
                p = '{name}: {type}\n{desc}'.format(**info)
                parts.append(p)
                parts.append('')
            new_body = '\n'.join(parts)
        if key in {'Returns', 'Yields'}:
            retinfos = list(
                docscrape_google.parse_google_retblock(old_body))
            parts = []
            for info in retinfos:
                info['desc'] = ub.indent(info['desc'])
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

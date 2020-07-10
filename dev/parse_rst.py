"""
It might be a good idea to be able to parse RST blocks and doctest them.
"""


def parse_rst_codeblocks(fpath):
    """
    import ubelt as ub
    fpath = ub.expandpath('$HOME/code/xdoctest/README.rst')
    """

    # Proably a better way to to this

    with open(fpath, 'r') as file:
        text = file.read()

    blocks = []

    valid_code_headers = [
        '.. code-block::',
        '.. code::',
    ]

    curr = None
    for lineno, line in enumerate(text.split('\n')):

        found_header = None

        for header in valid_code_headers:
            if line.startswith(header):
                found_header = header

        if found_header is not None:
            curr = {
                'lineno_start': lineno,
                'lineno_end': None,
                'lines': [],
                'header': line,
                'language': line.replace(found_header, '').strip()
            }
        else:
            if curr is not None:
                if line and not line.startswith(' '):
                    curr['lines']
                    curr['lineno_end'] = lineno - 1
                    blocks.append(curr)
                    curr = None
                else:
                    curr['lines'].append(line)

    # import ubelt as ub
    # print('blocks = {}'.format(ub.repr2(blocks, nl=3)))
    return blocks

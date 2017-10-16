"""
http://docs.readthedocs.io/en/latest/getting_started.html#in-rst
pip install sphinx sphinx-autobuild
pip install sphinxcontrib-napoleon
pip install sphinx_rtd_theme

"""


def initialize_docs():
    from os.path import join
    import setup
    setupkw = setup.setupkw
    full_version = setup.parse_version()
    short_version = '.'.join(full_version.split('.')[0:2])

    doc_dpath = join('.', 'docs')

    exe = 'sphinx-apidoc'
    args = [
        exe,
        '--force',
        '--full',
        '--output-dir="{}"'.format(doc_dpath),
        '--doc-author="{}"'.format(setupkw['author']),
        '--doc-version="{}"'.format(short_version),
        '--doc-release="{}"'.format(full_version),
        '--maxdepth="8"',
        # '--ext-autodoc',
        # '--ext-ifconfig',
        # '--ext-githubpages',
        # '--ext-mathjax',
        setupkw['name'],
    ]
    cmdstr = ' '.join(args)

    import ubelt as ub
    result = ub.cmd(cmdstr, verbose=2)
    assert result['ret'] == 0


def modify_conf():
    """
    pip install redbaron
    """
    import redbaron
    import ubelt as ub
    conf_path = 'docs/conf.py'

    source = ub.readfrom(conf_path)
    red = redbaron.RedBaron(source)

    # Insert custom extensions
    extra_extensions = [
        '"sphinxcontrib.napoleon"'
    ]

    ext_node = red.find('name', value='extensions').parent
    ext_node.value.value.extend(extra_extensions)

    # Overwrite theme to read-the-docs
    theme_node = red.find('name', value='html_theme').parent
    theme_node.value.value = '"sphinx_rtd_theme"'

    ub.writeto(conf_path, red.dumps())

def _parse_changelog(fpath):
    """
    Helper to parse the changelog for the version to verify versions agree.

    CommandLine:
        xdoctest -m dev/parse_changelog.py _parse_changelog --dev
    """
    try:
        from packaging.version import parse as LooseVersion
    except ImportError:
        from distutils.version import LooseVersion
    import re

    pat = re.compile(r'#.*Version ([0-9]+\.[0-9]+\.[0-9]+)')
    # We can statically modify this to a constant value when we deploy
    versions = []
    with open(fpath, 'r') as file:
        for line in file.readlines():
            line = line.rstrip()
            if line:
                parsed = pat.search(line)
                if parsed:
                    print('parsed = {!r}'.format(parsed))
                    try:
                        version_text = parsed.groups()[0]
                        version = LooseVersion(version_text)
                        versions.append(version)
                    except Exception:
                        print('Failed to parse = {!r}'.format(line))

    import pprint

    print('versions = {}'.format(pprint.pformat(versions)))
    assert sorted(versions)[::-1] == versions

    import xdoctest

    changelog_version = versions[0]
    module_version = LooseVersion(xdoctest.__version__)
    print('changelog_version = {!r}'.format(changelog_version))
    print('module_version = {!r}'.format(module_version))
    assert changelog_version == module_version


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdoctest/dev/parse_changelog.py
    """
    fpath = 'CHANGELOG.md'
    _parse_changelog(fpath)

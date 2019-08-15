
def _pkgutil_submodule_names(modpath, with_pkg=False, with_mod=True):
    """
    Ignore:
        x = sorted(submodule_paths(modname_to_modpath('ubelt')))
        y = sorted(_pkgutil_submodule_names(modname_to_modpath('ubelt')))
        x = [modpath_to_modname(p, hide_init=False, hide_main=False) for p in x]
        print('x = {!r}'.format(x))
        print('y = {!r}'.format(y))

    Notes:
        this will take into account pyc files, we choose not to.
    """
    package_name = modpath_to_modname(modpath)
    if isfile(modpath):
        # If input is a file, just return it
        yield package_name
    else:
        # Otherwise, if it is a package, find sub-packages and sub-modules
        import pkgutil
        # dont use the pkgutil version, as it is incompatible with pytest
        prefix = package_name + '.'
        walker = pkgutil.walk_packages([modpath], prefix=prefix,
                                       onerror=lambda x: None)  # nocover
        for importer, modname, ispkg in walker:
            if not ispkg and with_mod:
                yield modname
            elif ispkg and with_pkg:
                yield modname


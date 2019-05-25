"""
Most of these utilities exist in ubelt, but we copy them here to keep xdoctest
as a package with minimal dependencies, whereas ubelt includes a larger set of
utilities.

This __init__ file is generated using mkinit:

    mkinit xdoctest.utils
"""
from xdoctest.utils import util_import
from xdoctest.utils import util_misc
from xdoctest.utils import util_mixins
from xdoctest.utils import util_path
from xdoctest.utils import util_str
from xdoctest.utils import util_stream

from xdoctest.utils.util_import import (PythonPathContext,
                                        import_module_from_name,
                                        import_module_from_path,
                                        is_modname_importable,
                                        modname_to_modpath, modpath_to_modname,
                                        normalize_modpath, split_modpath,)
from xdoctest.utils.util_misc import (TempDoctest,)
from xdoctest.utils.util_mixins import (NiceRepr,)
from xdoctest.utils.util_path import (TempDir, ensuredir,)
from xdoctest.utils.util_str import (add_line_numbers, codeblock, color_text,
                                     ensure_unicode, highlight_code, indent,
                                     strip_ansi,)
from xdoctest.utils.util_stream import (CaptureStdout, CaptureStream,
                                        TeeStringIO,)

__all__ = ['CaptureStdout', 'CaptureStream', 'NiceRepr', 'PythonPathContext',
           'TeeStringIO', 'TempDir', 'TempDoctest', 'add_line_numbers',
           'codeblock', 'color_text', 'ensure_unicode', 'ensuredir',
           'highlight_code', 'import_module_from_name',
           'import_module_from_path', 'indent', 'is_modname_importable',
           'modname_to_modpath', 'modpath_to_modname', 'normalize_modpath',
           'split_modpath', 'strip_ansi', 'util_import', 'util_misc',
           'util_mixins', 'util_path', 'util_str', 'util_stream']

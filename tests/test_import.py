import os
import zipfile

from xdoctest.utils.util_import import import_module_from_path


def test_zip_module_import_from_path(tmp_path):
    archive_path = tmp_path / 'test.zip'
    with zipfile.ZipFile(archive_path, 'w') as archive:
        archive.writestr('zip_test_member.py', 'testvar = 42\n')
        archive.writestr('folder/zip_test_nested.py', 'testvar = 43\n')

    for sep, member, expected in [
        (':', 'zip_test_member.py', 42),
        (os.path.sep, 'folder/zip_test_nested.py', 43),
    ]:
        module = import_module_from_path(str(archive_path) + sep + member)
        assert module.testvar == expected

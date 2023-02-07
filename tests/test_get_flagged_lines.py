import pytest_check as check
from pii_check.pii_check_hook import get_flagged_lines


def test_get_flagged_lines():
    files = [
        "tests/test_data/dir_with_files/file_with_pii.txt", "tests/test_data/dir_with_files/file_without_pii.txt",
        "tests/test_data/dir_with_files/file_with_pii_flag_on", "tests/test_data/dir_with_files/file_with_pii_flag_off",
        "tests/test_data/dir_with_files/file_with_pii_flag", "tests/test_data/symlink_of_dir_with_files"
    ]
    res = get_flagged_lines(files)
    check.equal(res, [(1, 6, 'tests/test_data/dir_with_files/file_with_pii_flag')])


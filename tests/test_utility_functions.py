import pytest

from pii_check.pii_check_hook import get_ignored_lines


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("tests/test_data/dir_with_files/file_with_pii.txt", set()),
        ("tests/test_data/dir_with_files/file_without_pii.txt", set()),
        ("tests/test_data/dir_with_files/file_with_pii_flag", {1, 2, 3, 4, 5, 6}),
        ("tests/test_data/dir_with_files/file_with_mismatch_pii_flags", set()),
    ],
)
def test_get_ignored_lines(filename, expected):
    res = get_ignored_lines(filename)
    assert res == expected

"""Tests of the test repository file format (stage 3)."""
import os
import unittest

from depgraph.errors import RepositoryError
from depgraph.test_repo import load_test_repo, parse_test_repo
from helpers import make_temp_dir, write_file


class ParseTest(unittest.TestCase):
    """Parsing of the text of a test repository."""

    def test_packages_and_dependencies(self):
        packages = parse_test_repo("A: B C\nB: C\nC:\n")
        self.assertEqual(packages, {"A": ["B", "C"], "B": ["C"], "C": []})

    def test_comments_and_empty_lines(self):
        text = "# header\n\nA: B  # inline\n   \nB:\n"
        self.assertEqual(parse_test_repo(text), {"A": ["B"], "B": []})

    def test_duplicate_dependencies_are_merged(self):
        self.assertEqual(parse_test_repo("A: B B\n"), {"A": ["B"]})

    def test_windows_line_endings(self):
        packages = parse_test_repo("A: B\r\nB:\r\n")
        self.assertEqual(packages, {"A": ["B"], "B": []})

    def test_multi_letter_names(self):
        self.assertEqual(parse_test_repo("AB: CD\n"), {"AB": ["CD"]})

    def test_line_without_colon(self):
        with self.assertRaisesRegex(RepositoryError, "line 2: expected"):
            parse_test_repo("A: B\nB C\n")

    def test_invalid_package_name(self):
        with self.assertRaisesRegex(RepositoryError, "invalid package name"):
            parse_test_repo("a: B\n")

    def test_invalid_dependency_name(self):
        with self.assertRaisesRegex(RepositoryError, "dependency name 'b'"):
            parse_test_repo("A: b\n")

    def test_package_described_twice(self):
        with self.assertRaisesRegex(RepositoryError, "line 2: package A"):
            parse_test_repo("A: B\nA: C\n")

    def test_empty_file_has_no_packages(self):
        self.assertEqual(parse_test_repo(""), {})


class LoadTest(unittest.TestCase):
    """Reading of the file."""

    def test_load(self):
        path = write_file(make_temp_dir(self), "r.txt", "A: B\n")
        self.assertEqual(load_test_repo(path), {"A": ["B"]})

    def test_bom_is_ignored(self):
        path = os.path.join(make_temp_dir(self), "r.txt")
        with open(path, "wb") as file:
            file.write(b"\xef\xbb\xbfA: B\n")
        self.assertEqual(load_test_repo(path), {"A": ["B"]})

    def test_missing_file(self):
        path = os.path.join(make_temp_dir(self), "none.txt")
        with self.assertRaisesRegex(RepositoryError, "cannot read"):
            load_test_repo(path)

    def test_binary_file(self):
        path = os.path.join(make_temp_dir(self), "r.bin")
        with open(path, "wb") as file:
            file.write(b"\xff\xfe\x00\x80")
        with self.assertRaisesRegex(RepositoryError, "not a UTF-8"):
            load_test_repo(path)


if __name__ == "__main__":
    unittest.main()

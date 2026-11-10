"""Tests of the command-line parameters (stage 1)."""
import os
import unittest

from depgraph.config import (
    DEFAULT_DEPTH, DEFAULT_OUTPUT, DEFAULT_REPO, MODE_TEST, MODE_URL,
    parse_args,
)
from depgraph.errors import ConfigError
from helpers import make_temp_dir, write_file


class ParseTest(unittest.TestCase):
    """Valid command lines."""

    def test_defaults(self):
        config = parse_args(["-p", "org.example:app:1.0"])
        self.assertEqual(config.repo, DEFAULT_REPO)
        self.assertEqual(config.mode, MODE_URL)
        self.assertEqual(config.output, DEFAULT_OUTPUT)
        self.assertEqual(config.max_depth, DEFAULT_DEPTH)
        self.assertEqual(config.name_filter, "")

    def test_all_options(self):
        config = parse_args([
            "--package", "org.example:app:1.0",
            "--repo", "https://example.org/maven/",
            "--mode", "url", "--output", "out.png",
            "--max-depth", "5", "--filter", "log",
        ])
        self.assertEqual(config.repo, "https://example.org/maven")
        self.assertEqual(config.max_depth, 5)
        self.assertEqual(config.name_filter, "log")

    def test_file_url_is_accepted(self):
        config = parse_args(["-p", "a.b:c:1", "-r", "file:///tmp/repo"])
        self.assertEqual(config.repo, "file:///tmp/repo")

    def test_test_mode_with_existing_file(self):
        path = write_file(make_temp_dir(self), "repo.txt", "A: B\n")
        config = parse_args(["-p", "A", "-m", "test", "-r", path])
        self.assertEqual(config.mode, MODE_TEST)
        self.assertEqual(config.repo, path)


class PackageErrorTest(unittest.TestCase):
    """Invalid package names."""

    def test_package_is_required(self):
        with self.assertRaisesRegex(ConfigError, "--package"):
            parse_args([])

    def test_maven_package_needs_three_parts(self):
        with self.assertRaisesRegex(ConfigError, "groupId:artifactId"):
            parse_args(["-p", "org.example:app"])

    def test_maven_package_rejects_bad_characters(self):
        with self.assertRaisesRegex(ConfigError, "invalid package"):
            parse_args(["-p", "org.example:ap p:1.0"])

    def test_maven_package_rejects_empty_part(self):
        with self.assertRaisesRegex(ConfigError, "invalid package"):
            parse_args(["-p", "org.example::1.0"])

    def test_test_package_must_be_capital_letters(self):
        path = write_file(make_temp_dir(self), "repo.txt", "A:\n")
        for name in ("a", "A1", "org.example:app:1.0", ""):
            with self.assertRaisesRegex(ConfigError, "invalid test package"):
                parse_args(["-p", name, "-m", "test", "-r", path])


class RepoErrorTest(unittest.TestCase):
    """Invalid repository parameters."""

    def test_unknown_scheme(self):
        with self.assertRaisesRegex(ConfigError, "scheme must be"):
            parse_args(["-p", "a.b:c:1", "-r", "ftp://example.org/repo"])

    def test_plain_text_is_not_a_url(self):
        with self.assertRaisesRegex(ConfigError, "invalid repository URL"):
            parse_args(["-p", "a.b:c:1", "-r", "not a url"])

    def test_http_url_needs_a_host(self):
        with self.assertRaisesRegex(ConfigError, "no host"):
            parse_args(["-p", "a.b:c:1", "-r", "https:///path"])

    def test_test_mode_needs_repo(self):
        with self.assertRaisesRegex(ConfigError, "requires --repo"):
            parse_args(["-p", "A", "-m", "test"])

    def test_missing_test_file(self):
        path = os.path.join(make_temp_dir(self), "missing.txt")
        with self.assertRaisesRegex(ConfigError, "not found"):
            parse_args(["-p", "A", "-m", "test", "-r", path])

    def test_test_repo_is_a_directory(self):
        path = make_temp_dir(self)
        with self.assertRaisesRegex(ConfigError, "is a directory"):
            parse_args(["-p", "A", "-m", "test", "-r", path])

    def test_unknown_mode(self):
        with self.assertRaisesRegex(ConfigError, "invalid choice"):
            parse_args(["-p", "A", "-m", "remote"])


class OutputAndLimitsErrorTest(unittest.TestCase):
    """Invalid output, depth and unknown options."""

    def test_output_needs_png_extension(self):
        with self.assertRaisesRegex(ConfigError, r"\.png extension"):
            parse_args(["-p", "a.b:c:1", "-o", "graph.jpg"])

    def test_output_directory_must_exist(self):
        path = os.path.join(make_temp_dir(self), "no", "graph.png")
        with self.assertRaisesRegex(ConfigError, "does not exist"):
            parse_args(["-p", "a.b:c:1", "-o", path])

    def test_output_must_not_be_a_directory(self):
        path = make_temp_dir(self)
        os.mkdir(os.path.join(path, "x.png"))
        with self.assertRaisesRegex(ConfigError, "is a directory"):
            parse_args(["-p", "a.b:c:1", "-o", os.path.join(path, "x.png")])

    def test_depth_must_be_an_integer(self):
        with self.assertRaisesRegex(ConfigError, "must be an integer"):
            parse_args(["-p", "a.b:c:1", "-d", "deep"])

    def test_depth_must_be_positive(self):
        for value in ("0", "-2"):
            with self.assertRaisesRegex(ConfigError, "at least 1"):
                parse_args(["-p", "a.b:c:1", "-d", value])

    def test_unknown_option(self):
        with self.assertRaisesRegex(ConfigError, "unrecognized"):
            parse_args(["-p", "a.b:c:1", "--color"])


if __name__ == "__main__":
    unittest.main()

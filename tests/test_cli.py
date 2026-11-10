"""Tests of the command-line interface."""
import os
import unittest

from helpers import EXAMPLES_DIR, file_url, make_temp_dir, run_cli

REPO_URL = file_url(os.path.join(EXAMPLES_DIR, "maven-repo"))


class CliErrorTest(unittest.TestCase):
    """Exit codes and messages for invalid parameters."""

    def test_error_goes_to_stderr_with_code_2(self):
        code, out, err = run_cli(["-p", "bad"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("error: invalid package 'bad'"))

    def test_every_parameter_has_an_error(self):
        directory = make_temp_dir(self)
        cases = [
            ["-p", "bad"],
            ["-p", "a.b:c:1", "-r", "ftp://x"],
            ["-p", "a.b:c:1", "-m", "none"],
            ["-p", "a.b:c:1", "-o", os.path.join(directory, "x.txt")],
            ["-p", "a.b:c:1", "-d", "0"],
        ]
        for argv in cases:
            code, _out, err = run_cli(argv)
            self.assertEqual(code, 2, argv)
            self.assertTrue(err.startswith("error: "), argv)


class DirectDependenciesTest(unittest.TestCase):
    """Stage 2: direct dependencies of a Maven package."""

    def test_direct_dependencies_are_printed(self):
        code, out, err = run_cli(
            ["-p", "org.example:shop-app:1.0.0", "-r", REPO_URL])
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [
            "Direct dependencies of org.example:shop-app:1.0.0:",
            "  org.example:shop-web:1.0.0",
            "  org.example:shop-db:1.0.0",
            "  org.example:ghost:9.9.9",
            "  org.example:logging-api:1.0.0",
        ])
        self.assertEqual(err, "")

    def test_package_without_dependencies(self):
        code, out, _err = run_cli(
            ["-p", "org.example:logging-api:1.0.0", "-r", REPO_URL])
        self.assertEqual(code, 0)
        self.assertIn("  (none)", out)

    def test_missing_package_is_an_error(self):
        code, out, err = run_cli(
            ["-p", "org.example:nope:1.0", "-r", REPO_URL])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("error: not found:", err)

    def test_unreachable_repository_is_an_error(self):
        code, _out, err = run_cli(
            ["-p", "org.example:app:1.0", "-r", "http://127.0.0.1:9"])
        self.assertEqual(code, 1)
        self.assertIn("error: cannot read http://127.0.0.1:9/", err)


if __name__ == "__main__":
    unittest.main()

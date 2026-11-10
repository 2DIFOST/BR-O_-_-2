"""Tests of the command-line interface (stage 1)."""
import os
import unittest

from helpers import make_temp_dir, run_cli


class CliTest(unittest.TestCase):
    """Exit codes and messages of the tool."""

    def test_parameters_are_printed(self):
        code, out, err = run_cli(["-p", "a.b:c:1", "-d", "2"])
        self.assertEqual(code, 0)
        self.assertIn("package: a.b:c:1\n", out)
        self.assertIn("max-depth: 2\n", out)
        self.assertEqual(err, "")

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


if __name__ == "__main__":
    unittest.main()

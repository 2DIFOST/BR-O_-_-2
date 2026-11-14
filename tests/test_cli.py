"""Tests of the command-line interface."""
import os
import unittest
from unittest import mock

from helpers import (
    EXAMPLES_DIR, file_url, make_temp_dir, run_cli, write_file,
)

REPO_URL = file_url(os.path.join(EXAMPLES_DIR, "maven-repo"))
DIAMOND = os.path.join(EXAMPLES_DIR, "test-repos", "diamond.txt")


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


class DrawTest(unittest.TestCase):
    """The option --draw (the real rendering is mocked)."""

    def test_draw_saves_text_and_image(self):
        image = os.path.join(make_temp_dir(self), "d.png")

        def fake_draw(text, path, renderer):
            self.assertTrue(text.startswith("flowchart TD"))
            self.assertEqual(renderer, "online")
            return path[:-3] + "mmd"

        with mock.patch("depgraph.cli.draw", side_effect=fake_draw):
            code, out, _err = run_cli([
                "-p", "A", "-m", "test", "-r", DIAMOND, "--draw", "-o",
                image, "--renderer", "online"])
        self.assertEqual(code, 0)
        self.assertIn(f"Mermaid text: {image[:-3]}mmd", out.splitlines())
        self.assertIn(f"Image: {image}", out.splitlines())

    def test_nothing_is_drawn_without_the_option(self):
        with mock.patch("depgraph.cli.draw") as draw:
            run_cli(["-p", "A", "-m", "test", "-r", DIAMOND])
        draw.assert_not_called()

    def test_rendering_error_has_code_3(self):
        directory = make_temp_dir(self)
        image = os.path.join(directory, "d.png")
        with mock.patch("shutil.which", return_value=None):
            code, _out, err = run_cli([
                "-p", "A", "-m", "test", "-r", DIAMOND, "--draw", "-o",
                image, "--renderer", "mmdc"])
        self.assertEqual(code, 3)
        self.assertTrue(err.startswith("error: mmdc (Mermaid CLI)"))
        self.assertTrue(os.path.isfile(os.path.join(directory, "d.mmd")))

    def test_draw_and_reverse_are_exclusive(self):
        code, _out, err = run_cli(
            ["-p", "A", "-m", "test", "-r", DIAMOND, "--draw", "-R", "D"])
        self.assertEqual(code, 2)
        self.assertEqual(
            err, "error: --draw cannot be combined with --reverse\n")

    def test_unknown_renderer(self):
        code, _out, _err = run_cli(
            ["-p", "A", "-m", "test", "-r", DIAMOND, "--renderer", "x"])
        self.assertEqual(code, 2)


class MavenModeTest(unittest.TestCase):
    """Dependency graph of a Maven package (file:// repository)."""

    def test_transitive_graph_is_printed(self):
        code, out, _err = run_cli(
            ["-p", "org.example:shop-web:1.0.0", "-r", REPO_URL, "-d", "2"])
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(
            lines[0],
            "Dependency graph of org.example:shop-web:1.0.0 "
            "(max depth 2, no filter)")
        self.assertIn("Level 0: org.example:shop-web:1.0.0", lines)
        self.assertIn(
            "  org.example:json-lib:4.0.0 -> org.example:common-utils:1.2.0",
            lines)
        self.assertIn("Cycles: none", lines)

    def test_different_versions_are_different_packages(self):
        _code, out, _err = run_cli(
            ["-p", "org.example:shop-app:1.0.0", "-r", REPO_URL])
        self.assertIn("org.example:common-utils:1.1.0", out)
        self.assertIn("org.example:common-utils:1.2.0", out)

    def test_filter_by_group_and_artifact(self):
        _code, out, _err = run_cli(
            ["-p", "org.example:shop-app:1.0.0", "-r", REPO_URL,
             "-f", "common-utils"])
        self.assertNotIn("common-utils", out.split("\n", 1)[1])
        self.assertIn("filter 'common-utils'", out)

    def test_missing_dependency_is_a_warning(self):
        code, _out, err = run_cli(
            ["-p", "org.example:shop-app:1.0.0", "-r", REPO_URL, "-d", "2"])
        self.assertEqual(code, 0)
        self.assertIn("warning: org.example:ghost:9.9.9: not found:", err)

    def test_cycle_of_maven_packages(self):
        code, out, _err = run_cli(
            ["-p", "org.example:cycle-a:1.0.0", "-r", REPO_URL])
        self.assertEqual(code, 0)
        self.assertIn(
            "  org.example:cycle-a:1.0.0 -> org.example:cycle-b:1.0.0 -> "
            "org.example:cycle-c:1.0.0 -> org.example:cycle-a:1.0.0", out)

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


class TestModeTest(unittest.TestCase):
    """Dependency graph from a test repository file."""

    def run_test_mode(self, name, *extra):
        """Run the tool on an example test repository."""
        path = os.path.join(EXAMPLES_DIR, "test-repos", name)
        return run_cli(["-p", "A", "-m", "test", "-r", path, *extra])

    def test_diamond(self):
        code, out, _err = self.run_test_mode("diamond.txt")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[1:], [
            "Packages: 4, dependencies: 4",
            "Level 0: A", "Level 1: B, C", "Level 2: D",
            "Dependencies:",
            "  A -> B", "  A -> C", "  B -> D", "  C -> D",
            "Cycles: none",
        ])

    def test_cycle(self):
        _code, out, _err = self.run_test_mode("cycle.txt")
        self.assertIn("Cycles: 1", out)
        self.assertIn("  A -> B -> C -> A", out)

    def test_self_loop(self):
        _code, out, _err = self.run_test_mode("self-loop.txt")
        self.assertIn("  A -> A", out.splitlines())
        self.assertIn("Cycles: 2", out)

    def test_depth(self):
        _code, out, _err = self.run_test_mode("chain.txt", "-d", "2")
        self.assertIn("Packages: 3, dependencies: 2", out)
        self.assertNotIn("Level 3", out)
        self.assertNotIn("-> D", out)

    def test_filter(self):
        _code, out, _err = self.run_test_mode("filter.txt", "-f", "X")
        self.assertIn("Packages: 4, dependencies: 3", out)
        self.assertNotIn("X", out.split("\n", 1)[1])
        _code, out, _err = self.run_test_mode("filter.txt", "-f", "Y")
        self.assertNotIn("Y", out.split("\n", 1)[1])

    def test_root_excluded_by_filter(self):
        code, _out, err = self.run_test_mode("diamond.txt", "-f", "A")
        self.assertEqual(code, 2)
        self.assertIn("excludes the analyzed package A", err)

    def test_unknown_root_package(self):
        path = os.path.join(EXAMPLES_DIR, "test-repos", "diamond.txt")
        code, _out, err = run_cli(["-p", "Z", "-m", "test", "-r", path])
        self.assertEqual(code, 1)
        self.assertIn("package Z is not described", err)

    def test_invalid_file(self):
        path = write_file(make_temp_dir(self), "bad.txt", "A B\n")
        code, _out, err = run_cli(["-p", "A", "-m", "test", "-r", path])
        self.assertEqual(code, 1)
        self.assertIn("line 1: expected", err)


if __name__ == "__main__":
    unittest.main()

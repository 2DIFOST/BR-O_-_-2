"""Tests of the reverse dependencies (stage 4)."""
import os
import unittest

from depgraph.errors import PackageNotFoundError
from depgraph.graph import build_graph
from depgraph.report import format_reverse
from depgraph.reverse import reverse_dependencies
from depgraph.sources import GraphFileSource
from depgraph.test_repo import parse_test_repo
from helpers import EXAMPLES_DIR, file_url, run_cli

REPO_URL = file_url(os.path.join(EXAMPLES_DIR, "maven-repo"))
DIAMOND = os.path.join(EXAMPLES_DIR, "test-repos", "diamond.txt")


def reverse_of(text, target, root="A", depth=10, name_filter=""):
    """Return the reverse dependencies of a package of a test repository."""
    source = GraphFileSource(parse_test_repo(text))
    graph = build_graph(source, root, depth, name_filter)
    return reverse_dependencies(graph, target)


class ReverseGraphTest(unittest.TestCase):
    """Search of the dependents with the BFS of the previous stage."""

    def test_levels_are_distances_from_the_package(self):
        result = reverse_of("A: B C\nB: D\nC: D\nD:\n", "D")
        self.assertEqual(result.levels(), [["D"], ["B", "C"], ["A"]])

    def test_root_has_no_dependents(self):
        result = reverse_of("A: B\nB:\n", "A")
        self.assertEqual(result.levels(), [["A"]])

    def test_only_packages_of_the_graph_are_considered(self):
        text = "A: B\nB:\nH: B\n"
        self.assertEqual(reverse_of(text, "B").levels(), [["B"], ["A"]])

    def test_depth_limit_of_the_graph_is_respected(self):
        text = "A: B\nB: C\nC: D\nD:\n"
        result = reverse_of(text, "B", depth=2)
        self.assertEqual(result.levels(), [["B"], ["A"]])
        with self.assertRaises(PackageNotFoundError):
            reverse_of(text, "D", depth=2)

    def test_filtered_packages_are_not_dependents(self):
        text = "A: B X\nX: B\nB:\n"
        result = reverse_of(text, "B", name_filter="X")
        self.assertEqual(result.levels(), [["B"], ["A"]])

    def test_cycle_does_not_loop_forever(self):
        result = reverse_of("A: B\nB: C\nC: A\n", "C")
        self.assertEqual(result.levels(), [["C"], ["B"], ["A"]])

    def test_self_dependency(self):
        result = reverse_of("A: A\n", "A")
        self.assertEqual(result.levels(), [["A"]])

    def test_unknown_package_is_an_error(self):
        with self.assertRaisesRegex(PackageNotFoundError, "package Z is not"):
            reverse_of("A: B\nB:\n", "Z")

    def test_long_chain_without_recursion(self):
        names = ["A" * length for length in range(1, 2001)]
        text = "".join(f"{one}: {two}\n"
                       for one, two in zip(names, names[1:]))
        result = reverse_of(text, names[-1], root="A", depth=5000)
        self.assertEqual(len(result.depth), len(names))


class ReverseReportTest(unittest.TestCase):
    """Text of the report."""

    def test_report_lines(self):
        result = reverse_of("A: B C\nB: D\nC: D\nD:\n", "D")
        self.assertEqual(format_reverse(result, "Title"), [
            "Title",
            "Dependent packages: 3",
            "Level 1: B, C",
            "Level 2: A",
            "Dependencies:",
            "  B -> D",
            "  C -> D",
            "  A -> B",
            "  A -> C",
        ])

    def test_report_without_dependents(self):
        lines = format_reverse(reverse_of("A: B\nB:\n", "A"), "Title")
        self.assertEqual(lines, [
            "Title", "Dependent packages: 0", "No package depends on A"])


class ReverseCliTest(unittest.TestCase):
    """The option --reverse in the command line."""

    def test_test_mode(self):
        code, out, err = run_cli(
            ["-p", "A", "-m", "test", "-r", DIAMOND, "-R", "D"])
        self.assertEqual((code, err), (0, ""))
        lines = out.splitlines()
        self.assertEqual(lines[0], "Reverse dependencies of D in the graph "
                         "of A (max depth 3, no filter)")
        self.assertIn("Level 1: B, C", lines)
        self.assertIn("Level 2: A", lines)

    def test_maven_mode(self):
        code, out, _err = run_cli([
            "-p", "org.example:shop-app:1.0.0", "-r", REPO_URL,
            "--reverse", "org.example:common-utils:1.2.0"])
        self.assertEqual(code, 0)
        self.assertIn(
            "Level 1: org.example:shop-web:1.0.0, "
            "org.example:json-lib:4.0.0", out)

    def test_package_outside_the_graph(self):
        code, out, err = run_cli(
            ["-p", "A", "-m", "test", "-r", DIAMOND, "-R", "X"])
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(
            err, "error: package X is not in the dependency graph of A\n")

    def test_invalid_package_name(self):
        code, _out, err = run_cli(
            ["-p", "A", "-m", "test", "-r", DIAMOND, "-R", "d"])
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith("error: invalid test package 'd'"))

    def test_without_option_the_graph_is_printed(self):
        _code, out, _err = run_cli(["-p", "A", "-m", "test", "-r", DIAMOND])
        self.assertTrue(out.startswith("Dependency graph of A"))


if __name__ == "__main__":
    unittest.main()

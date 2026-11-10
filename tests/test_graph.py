"""Tests of the BFS, depth limit, filter and cycles (stage 3)."""
import unittest

from depgraph.errors import ConfigError, PackageNotFoundError, RepositoryError
from depgraph.graph import build_graph, find_cycles
from depgraph.sources import GraphFileSource
from depgraph.test_repo import parse_test_repo


CHAIN_LENGTH = 3000


def letters(number):
    """Return a unique name made of capital letters for the number."""
    return "".join(chr(ord("A") + int(digit)) for digit in str(number))


def graph_of(text, root="A", depth=10, name_filter=""):
    """Build a graph from the text of a test repository."""
    source = GraphFileSource(parse_test_repo(text))
    return build_graph(source, root, depth, name_filter)


class BuildTest(unittest.TestCase):
    """Order, depth and transitive dependencies."""

    def test_transitive_dependencies_in_bfs_order(self):
        graph = graph_of("A: B C\nB: D\nC: E\nD:\nE:\n")
        self.assertEqual(list(graph.depth), ["A", "B", "C", "D", "E"])
        self.assertEqual(graph.depth, {"A": 0, "B": 1, "C": 1, "D": 2, "E": 2})

    def test_levels(self):
        graph = graph_of("A: B C\nB: D\nC: D\nD:\n")
        self.assertEqual(graph.levels(), [["A"], ["B", "C"], ["D"]])

    def test_shared_dependency_is_one_node_with_two_edges(self):
        graph = graph_of("A: B C\nB: D\nC: D\nD:\n")
        self.assertEqual(len(graph.depth), 4)
        self.assertEqual(graph.edges, [
            ("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])

    def test_shortest_depth_wins(self):
        graph = graph_of("A: B D\nB: C\nC: D\nD:\n")
        self.assertEqual(graph.depth["D"], 1)

    def test_package_without_dependencies(self):
        graph = graph_of("A:\n")
        self.assertEqual(graph.depth, {"A": 0})
        self.assertEqual(graph.edges, [])

    def test_undeclared_dependency_is_a_leaf(self):
        graph = graph_of("A: Z\n")
        self.assertEqual(graph.edges, [("A", "Z")])

    def test_unreachable_packages_are_not_included(self):
        graph = graph_of("A: B\nB:\nC: A\n")
        self.assertNotIn("C", graph.depth)

    def test_long_chain_does_not_use_recursion(self):
        names = [letters(number) for number in range(CHAIN_LENGTH)]
        lines = [f"{name}: {after}" for name, after in zip(names, names[1:])]
        graph = graph_of("\n".join(lines), root=names[0], depth=CHAIN_LENGTH)
        self.assertEqual(len(graph.depth), CHAIN_LENGTH)


class DepthTest(unittest.TestCase):
    """Maximum depth of the analysis."""

    TEXT = "A: B\nB: C\nC: D\nD: E\nE:\n"

    def test_depth_one_gives_direct_dependencies(self):
        graph = graph_of(self.TEXT, depth=1)
        self.assertEqual(graph.edges, [("A", "B")])
        self.assertEqual(list(graph.depth), ["A", "B"])

    def test_depth_limits_the_graph(self):
        graph = graph_of(self.TEXT, depth=3)
        self.assertEqual(list(graph.depth), ["A", "B", "C", "D"])
        self.assertEqual(graph.edges[-1], ("C", "D"))

    def test_depth_larger_than_graph(self):
        graph = graph_of(self.TEXT, depth=100)
        self.assertEqual(len(graph.depth), 5)


class FilterTest(unittest.TestCase):
    """Packages whose name contains the substring are ignored."""

    def test_filtered_package_and_its_dependencies_are_skipped(self):
        graph = graph_of("A: B X\nB: C\nX: D\nC:\nD:\n", name_filter="X")
        self.assertEqual(list(graph.depth), ["A", "B", "C"])
        self.assertEqual(graph.edges, [("A", "B"), ("B", "C")])

    def test_filter_applies_at_every_level(self):
        graph = graph_of("A: B\nB: Y C\nY:\nC:\n", name_filter="Y")
        self.assertNotIn("Y", graph.depth)

    def test_filter_matches_a_substring_of_a_longer_name(self):
        graph = graph_of("A: AB CD\nAB:\nCD:\n", name_filter="B")
        self.assertEqual(list(graph.depth), ["A", "CD"])

    def test_filter_that_excludes_the_root_is_an_error(self):
        with self.assertRaisesRegex(ConfigError, "excludes the analyzed"):
            graph_of("A: B\n", name_filter="A")

    def test_empty_filter_excludes_nothing(self):
        self.assertEqual(len(graph_of("A: B\n").depth), 2)

    def test_filter_is_case_sensitive(self):
        graph = graph_of("A: B\nB:\n", name_filter="b")
        self.assertIn("B", graph.depth)


class CycleTest(unittest.TestCase):
    """Cyclic dependencies."""

    def test_cycle_terminates_and_is_reported(self):
        graph = graph_of("A: B\nB: C\nC: A\n")
        self.assertEqual(list(graph.depth), ["A", "B", "C"])
        self.assertEqual(graph.edges[-1], ("C", "A"))
        self.assertEqual(find_cycles(graph), [["A", "B", "C", "A"]])

    def test_self_dependency(self):
        graph = graph_of("A: A B\nB:\n")
        self.assertEqual(find_cycles(graph), [["A", "A"]])

    def test_two_cycles(self):
        graph = graph_of("A: B C\nB: A\nC: A\n")
        self.assertEqual(len(find_cycles(graph)), 2)

    def test_cycle_not_through_the_root(self):
        graph = graph_of("A: B\nB: C\nC: B\n")
        self.assertEqual(find_cycles(graph), [["B", "C", "B"]])

    def test_acyclic_graph_has_no_cycles(self):
        graph = graph_of("A: B C\nB: D\nC: D\nD:\n")
        self.assertEqual(find_cycles(graph), [])

    def test_cycle_beyond_depth_is_not_visible(self):
        graph = graph_of("A: B\nB: A\n", depth=1)
        self.assertEqual(find_cycles(graph), [])


class FailingSource:
    """A source whose packages cannot be read."""

    warnings = []

    def dependencies(self, node):
        """Fail for every package except A."""
        if node == "A":
            return ["B"]
        raise PackageNotFoundError(f"{node} is gone")

    def package_name(self, node):
        """Return the node itself."""
        return node


class ErrorTest(unittest.TestCase):
    """Packages that cannot be read."""

    def test_problem_with_a_dependency_is_a_warning(self):
        graph = build_graph(FailingSource(), "A", 3)
        self.assertEqual(graph.edges, [("A", "B")])
        self.assertEqual(graph.warnings, ["B: B is gone"])

    def test_problem_with_the_root_is_an_error(self):
        with self.assertRaises(RepositoryError):
            build_graph(FailingSource(), "Z", 3)


if __name__ == "__main__":
    unittest.main()

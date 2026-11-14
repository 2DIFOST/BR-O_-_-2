"""Tests of the Mermaid text of a graph (stage 5)."""
import unittest

from depgraph.graph import Graph, build_graph
from depgraph.mermaid import escape_label, to_mermaid
from depgraph.sources import GraphFileSource
from depgraph.test_repo import parse_test_repo


def graph_of(text, root="A", depth=10):
    """Build the graph of a test repository."""
    return build_graph(GraphFileSource(parse_test_repo(text)), root, depth)


class MermaidTest(unittest.TestCase):
    """Nodes, edges and the highlighted root."""

    def test_diamond(self):
        text = to_mermaid(graph_of("A: B C\nB: D\nC: D\nD:\n"))
        self.assertEqual(text.splitlines(), [
            "flowchart TD",
            '    n0["A"]',
            '    n1["B"]',
            '    n2["C"]',
            '    n3["D"]',
            "    n0 --> n1",
            "    n0 --> n2",
            "    n1 --> n3",
            "    n2 --> n3",
            "    classDef root fill:#fde68a,stroke:#b45309,stroke-width:2px",
            "    class n0 root",
        ])

    def test_text_ends_with_a_newline(self):
        self.assertTrue(to_mermaid(graph_of("A:\n")).endswith("\n"))

    def test_single_package(self):
        lines = to_mermaid(graph_of("A:\n")).splitlines()
        self.assertEqual(lines[1], '    n0["A"]')
        self.assertFalse(any("-->" in line for line in lines))

    def test_cycle_is_drawn_as_an_edge_back(self):
        text = to_mermaid(graph_of("A: B\nB: A\n"))
        self.assertIn("    n1 --> n0", text)

    def test_maven_names_are_kept_in_labels(self):
        graph = Graph("org.a:b:1.0", {"org.a:b:1.0": 0}, [])
        self.assertIn('n0["org.a:b:1.0"]', to_mermaid(graph))

    def test_node_identifiers_are_not_package_names(self):
        text = to_mermaid(graph_of("A: END\nEND:\n"))
        self.assertIn('n1["END"]', text)

    def test_quotes_are_escaped(self):
        self.assertEqual(escape_label('a"b'), "a#quot;b")


if __name__ == "__main__":
    unittest.main()

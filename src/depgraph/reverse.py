"""Reverse dependencies: the packages that depend on a given package."""
from .errors import PackageNotFoundError
from .graph import build_graph
from .sources import GraphFileSource


def reverse_dependencies(graph, target):
    """Return the graph of the packages that depend on ``target``.

    The edges of the dependency graph are reversed and the same BFS that
    builds the dependency graph is run from ``target``. The depth of a
    package in the result is its distance from ``target``, and an edge
    ``(package, dependent)`` means that ``dependent`` depends on
    ``package``. Raises PackageNotFoundError if ``target`` is not in the
    graph.
    """
    if target not in graph.depth:
        raise PackageNotFoundError(
            f"package {target} is not in the dependency graph of "
            f"{graph.root}")
    reversed_edges = GraphFileSource(graph.flipped().adjacency())
    return build_graph(reversed_edges, target, len(graph.depth))

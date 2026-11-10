"""Dependency graph: breadth-first construction and cycle detection."""
from collections import deque
from dataclasses import dataclass, field

from .errors import ConfigError, RepositoryError

VISITING = "visiting"
DONE = "done"


@dataclass
class Graph:
    """A dependency graph built from one root package.

    ``depth`` maps every package to its distance from the root and keeps
    the order in which packages were discovered; ``edges`` lists the
    dependencies ``(package, dependency)`` in discovery order.
    """

    root: str
    depth: dict
    edges: list
    warnings: list = field(default_factory=list)

    def adjacency(self):
        """Return a dictionary {package: [its dependencies]}."""
        result = {node: [] for node in self.depth}
        for source, target in self.edges:
            result[source].append(target)
        return result

    def levels(self):
        """Return the packages grouped by depth, level 0 first."""
        levels = []
        for node, depth in self.depth.items():
            while len(levels) <= depth:
                levels.append([])
            levels[depth].append(node)
        return levels

    def flipped(self):
        """Return the same graph with the direction of every edge reversed."""
        edges = [(target, source) for source, target in self.edges]
        return Graph(self.root, dict(self.depth), edges, list(self.warnings))


def is_filtered(source, node, name_filter):
    """Return True if the package name contains the filter substring."""
    return bool(name_filter) and name_filter in source.package_name(node)


def dependencies_of(source, node, root, warnings):
    """Return the dependencies of a package.

    A failure for the root package is an error; for any other package it
    only produces a warning and the package is treated as a leaf.
    """
    try:
        return source.dependencies(node)
    except RepositoryError as error:
        if node == root:
            raise
        warnings.append(f"{node}: {error}")
        return []


def build_graph(source, root, max_depth, name_filter=""):
    """Build the dependency graph with a non-recursive BFS.

    Packages deeper than ``max_depth`` are not visited, packages whose
    name contains ``name_filter`` are ignored. Every package is expanded
    only once, so cyclic dependencies cannot cause an endless loop.
    """
    if is_filtered(source, root, name_filter):
        raise ConfigError(
            f"filter '{name_filter}' excludes the analyzed package {root}")
    depth = {root: 0}
    edges = []
    known_edges = set()
    warnings = []
    queue = deque([root])
    while queue:
        node = queue.popleft()
        if depth[node] >= max_depth:
            continue
        for target in dependencies_of(source, node, root, warnings):
            if is_filtered(source, target, name_filter):
                continue
            if (node, target) not in known_edges:
                known_edges.add((node, target))
                edges.append((node, target))
            if target not in depth:
                depth[target] = depth[node] + 1
                queue.append(target)
    return Graph(root, depth, edges, warnings)


def advance(stack, path, state, children):
    """Make one step of the iterative DFS; return a found cycle or None."""
    node, iterator = stack[-1]
    target = next(iterator, None)
    if target is None:
        state[node] = DONE
        stack.pop()
        path.pop()
        return None
    if state.get(target) == VISITING:
        return path[path.index(target):] + [target]
    if target not in state:
        state[target] = VISITING
        stack.append((target, iter(children[target])))
        path.append(target)
    return None


def find_cycles(graph):
    """Return the cycles of the graph as closed paths ``[A, B, A]``.

    An iterative depth-first search is used; every back edge gives one
    cycle.
    """
    children = graph.adjacency()
    state = {}
    cycles = []
    for start in graph.depth:
        if start in state:
            continue
        state[start] = VISITING
        stack = [(start, iter(children[start]))]
        path = [start]
        while stack:
            cycle = advance(stack, path, state, children)
            if cycle is not None:
                cycles.append(cycle)
    return cycles

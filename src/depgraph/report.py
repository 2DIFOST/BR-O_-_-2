"""Text report about a dependency graph."""
from .graph import find_cycles

NO_CYCLES = "none"
ARROW = " -> "


def format_report(graph, title):
    """Return the lines that describe the graph.

    The report contains the number of packages and dependencies, the
    packages of every level, all dependencies and the cycles.
    """
    lines = [
        title,
        f"Packages: {len(graph.depth)}, dependencies: {len(graph.edges)}",
    ]
    for number, level in enumerate(graph.levels()):
        lines.append(f"Level {number}: {', '.join(level)}")
    lines.append("Dependencies:")
    lines.extend(f"  {source}{ARROW}{target}"
                 for source, target in graph.edges)
    if not graph.edges:
        lines.append("  (none)")
    lines.extend(format_cycles(find_cycles(graph)))
    return lines


def format_cycles(cycles):
    """Return the lines that describe the cyclic dependencies."""
    if not cycles:
        return [f"Cycles: {NO_CYCLES}"]
    lines = [f"Cycles: {len(cycles)}"]
    lines.extend(f"  {ARROW.join(cycle)}" for cycle in cycles)
    return lines

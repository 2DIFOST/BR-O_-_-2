"""Text representation of a dependency graph in the Mermaid language."""

HEADER = "flowchart TD"
ROOT_CLASS = "root"
ROOT_STYLE = "fill:#fde68a,stroke:#b45309,stroke-width:2px"
INDENT = "    "
QUOTE = "#quot;"


def escape_label(text):
    """Make the text safe inside a double-quoted Mermaid label."""
    return text.replace('"', QUOTE)


def to_mermaid(graph):
    """Return the Mermaid flowchart of the graph as text.

    Every package becomes a node ``n0``, ``n1``... labelled with its full
    name (generated identifiers avoid clashes with Mermaid keywords). An
    edge points from a package to its dependency; the analyzed package
    is highlighted.
    """
    ids = {node: f"n{number}" for number, node in enumerate(graph.depth)}
    lines = [HEADER]
    lines.extend(f'{INDENT}{ids[node]}["{escape_label(node)}"]'
                 for node in graph.depth)
    lines.extend(f"{INDENT}{ids[source]} --> {ids[target]}"
                 for source, target in graph.edges)
    lines.append(f"{INDENT}classDef {ROOT_CLASS} {ROOT_STYLE}")
    lines.append(f"{INDENT}class {ids[graph.root]} {ROOT_CLASS}")
    return "\n".join(lines) + "\n"

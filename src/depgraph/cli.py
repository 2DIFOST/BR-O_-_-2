"""Command-line interface of the tool."""
import sys

from .config import parse_args
from .errors import DepGraphError
from .graph import build_graph
from .mermaid import to_mermaid
from .render import draw
from .report import format_report, format_reverse
from .reverse import reverse_dependencies
from .sources import open_source

NO_FILTER = "no filter"


def describe_limits(config):
    """Return the depth and the filter of the analysis as text."""
    name_filter = NO_FILTER
    if config.name_filter:
        name_filter = f"filter '{config.name_filter}'"
    return f"max depth {config.max_depth}, {name_filter}"


def make_title(config):
    """Return the first line of the report."""
    return f"Dependency graph of {config.package} ({describe_limits(config)})"


def make_reverse_title(config):
    """Return the first line of the report of the reverse mode."""
    return (f"Reverse dependencies of {config.reverse} in the graph of "
            f"{config.package} ({describe_limits(config)})")


def report_warnings(warnings):
    """Print warnings to stderr."""
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)


def draw_graph(config, graph):
    """Save the Mermaid text and the PNG image of the graph."""
    text_path = draw(to_mermaid(graph), config.output, config.renderer)
    print(f"Mermaid text: {text_path}")
    print(f"Image: {config.output}")


def run(config):
    """Build the graph of the configured package and print the report."""
    source, root = open_source(config)
    graph = build_graph(source, root, config.max_depth, config.name_filter)
    if config.reverse:
        reverse = reverse_dependencies(graph, config.reverse)
        lines = format_reverse(reverse, make_reverse_title(config))
    else:
        lines = format_report(graph, make_title(config))
    for line in lines:
        print(line)
    if config.draw:
        draw_graph(config, graph)
    report_warnings(graph.warnings + source.warnings)


def main(argv=None):
    """Run the tool; return the process exit code."""
    try:
        run(parse_args(sys.argv[1:] if argv is None else argv))
    except DepGraphError as error:
        print(f"error: {error}", file=sys.stderr)
        return error.exit_code
    return 0

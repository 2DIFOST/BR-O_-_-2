"""Command-line interface of the tool."""
import sys

from .config import parse_args
from .errors import DepGraphError
from .graph import build_graph
from .report import format_report
from .sources import open_source

NO_FILTER = "no filter"


def make_title(config):
    """Return the first line of the report."""
    name_filter = NO_FILTER
    if config.name_filter:
        name_filter = f"filter '{config.name_filter}'"
    return (f"Dependency graph of {config.package} "
            f"(max depth {config.max_depth}, {name_filter})")


def report_warnings(warnings):
    """Print warnings to stderr."""
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)


def run(config):
    """Build the graph of the configured package and print the report."""
    source, root = open_source(config)
    graph = build_graph(source, root, config.max_depth, config.name_filter)
    for line in format_report(graph, make_title(config)):
        print(line)
    report_warnings(graph.warnings + source.warnings)


def main(argv=None):
    """Run the tool; return the process exit code."""
    try:
        run(parse_args(sys.argv[1:] if argv is None else argv))
    except DepGraphError as error:
        print(f"error: {error}", file=sys.stderr)
        return error.exit_code
    return 0

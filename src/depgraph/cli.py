"""Command-line interface of the tool."""
import sys

from .config import MODE_URL, parse_args
from .errors import DepGraphError
from .maven import MavenRepository
from .pom import parse_coordinate

NO_DEPENDENCIES = "(none)"


def print_direct_dependencies(coordinate, dependencies):
    """Print the direct dependencies of the package."""
    print(f"Direct dependencies of {coordinate}:")
    for dependency in dependencies:
        print(f"  {dependency}")
    if not dependencies:
        print(f"  {NO_DEPENDENCIES}")


def report_warnings(warnings):
    """Print warnings of the repository to stderr."""
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)


def run(config):
    """Print the direct dependencies of the configured package."""
    if config.mode != MODE_URL:
        raise DepGraphError("test mode is not supported yet")
    repository = MavenRepository(config.repo)
    coordinate = parse_coordinate(config.package)
    dependencies = repository.direct_dependencies(coordinate)
    print_direct_dependencies(coordinate, dependencies)
    report_warnings(repository.warnings)


def main(argv=None):
    """Run the tool; return the process exit code."""
    try:
        run(parse_args(sys.argv[1:] if argv is None else argv))
    except DepGraphError as error:
        print(f"error: {error}", file=sys.stderr)
        return error.exit_code
    return 0

"""Command-line interface of the tool."""
import sys

from .config import format_config, parse_args
from .errors import DepGraphError


def main(argv=None):
    """Run the tool; return the process exit code."""
    try:
        config = parse_args(sys.argv[1:] if argv is None else argv)
    except DepGraphError as error:
        print(f"error: {error}", file=sys.stderr)
        return error.exit_code
    for line in format_config(config):
        print(line)
    return 0

"""Command-line parameters of the tool and their validation."""
import argparse
import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from .errors import ConfigError

MODE_URL = "url"
MODE_TEST = "test"
MODES = (MODE_URL, MODE_TEST)
DEFAULT_REPO = "https://repo1.maven.org/maven2"
DEFAULT_OUTPUT = "graph.png"
DEFAULT_DEPTH = 3
MIN_DEPTH = 1
URL_SCHEMES = ("http", "https", "file")
NETWORK_SCHEMES = ("http", "https")
COORDINATE_PARTS = 3
COORDINATE_PART = re.compile(r"[A-Za-z0-9_.\-]+")
TEST_NAME = re.compile(r"[A-Z]+")


@dataclass(frozen=True)
class Config:
    """Validated parameters configured by the user."""

    package: str
    repo: str
    mode: str
    output: str
    max_depth: int
    name_filter: str
    reverse: str = ""


class ConfigParser(argparse.ArgumentParser):
    """Argument parser that reports problems as ConfigError."""

    def error(self, message):
        """Raise ConfigError instead of printing usage and exiting."""
        raise ConfigError(message)


def positive_int(text):
    """Convert the text to an integer not less than MIN_DEPTH."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"max depth must be an integer, got '{text}'") from None
    if value < MIN_DEPTH:
        raise argparse.ArgumentTypeError(
            f"max depth must be at least {MIN_DEPTH}, got {value}")
    return value


def build_parser():
    """Create the parser with all options of the tool."""
    parser = ConfigParser(
        prog="depgraph",
        description="Build the dependency graph of a Maven package.")
    parser.add_argument(
        "-p", "--package", required=True,
        help="package: groupId:artifactId:version, or A-Z name in test mode")
    parser.add_argument(
        "-r", "--repo",
        help="repository URL (http, https, file) or test repository file")
    parser.add_argument(
        "-m", "--mode", choices=MODES, default=MODE_URL,
        help="url: Maven repository, test: test repository file")
    parser.add_argument(
        "-o", "--output", default=DEFAULT_OUTPUT,
        help=f"PNG file with the graph (default: {DEFAULT_OUTPUT})")
    parser.add_argument(
        "-d", "--max-depth", type=positive_int, default=DEFAULT_DEPTH,
        help=f"maximum depth of the analysis (default: {DEFAULT_DEPTH})")
    parser.add_argument(
        "-f", "--filter", dest="name_filter", default="",
        metavar="SUBSTRING",
        help="skip packages whose name contains this substring")
    parser.add_argument(
        "-R", "--reverse", default="", metavar="PACKAGE",
        help="print the packages that depend on PACKAGE in the graph")
    return parser


def check_package(package, mode):
    """Check the package name for the given mode; return it."""
    if mode == MODE_TEST:
        if not TEST_NAME.fullmatch(package):
            raise ConfigError(
                f"invalid test package '{package}': "
                "use capital Latin letters, for example A")
        return package
    parts = package.split(":")
    valid = len(parts) == COORDINATE_PARTS and all(
        COORDINATE_PART.fullmatch(part) for part in parts)
    if not valid:
        raise ConfigError(
            f"invalid package '{package}': "
            "use groupId:artifactId:version")
    return package


def check_reverse(target, mode):
    """Check the package of the reverse mode; empty means it is off."""
    if not target:
        return ""
    return check_package(target, mode)


def check_url(repo):
    """Check that the repository URL is usable; return it without '/'."""
    parsed = urlparse(repo)
    if parsed.scheme not in URL_SCHEMES:
        raise ConfigError(
            f"invalid repository URL '{repo}': "
            f"scheme must be one of {', '.join(URL_SCHEMES)}")
    if parsed.scheme in NETWORK_SCHEMES and not parsed.netloc:
        raise ConfigError(f"invalid repository URL '{repo}': no host")
    if not parsed.netloc and not parsed.path:
        raise ConfigError(f"invalid repository URL '{repo}': no path")
    return repo.rstrip("/")


def check_test_file(path):
    """Check that the test repository file exists and is readable."""
    if os.path.isdir(path):
        raise ConfigError(f"test repository '{path}' is a directory")
    if not os.path.isfile(path):
        raise ConfigError(f"test repository file '{path}' not found")
    if not os.access(path, os.R_OK):
        raise ConfigError(f"test repository file '{path}' is not readable")
    return path


def check_repo(repo, mode):
    """Check the repository parameter for the given mode."""
    if mode == MODE_TEST:
        if repo is None:
            raise ConfigError("test mode requires --repo with a file path")
        return check_test_file(repo)
    return check_url(repo or DEFAULT_REPO)


def check_output(output):
    """Check that the PNG file can be created; return the path."""
    if not output.lower().endswith(".png"):
        raise ConfigError(f"output file '{output}' must have .png extension")
    if os.path.isdir(output):
        raise ConfigError(f"output '{output}' is a directory")
    directory = os.path.dirname(os.path.abspath(output))
    if not os.path.isdir(directory):
        raise ConfigError(f"output directory '{directory}' does not exist")
    if not os.access(directory, os.W_OK):
        raise ConfigError(f"output directory '{directory}' is not writable")
    return output


def parse_args(argv):
    """Parse and validate the command line; return a Config."""
    args = build_parser().parse_args(argv)
    return Config(
        package=check_package(args.package, args.mode),
        repo=check_repo(args.repo, args.mode),
        mode=args.mode,
        output=check_output(args.output),
        max_depth=args.max_depth,
        name_filter=args.name_filter,
        reverse=check_reverse(args.reverse, args.mode),
    )


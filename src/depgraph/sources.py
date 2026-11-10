"""Sources of dependency information used by the graph builder.

A source has two methods: ``dependencies(node)`` returns the names of the
direct dependencies and ``package_name(node)`` returns the part of a node
that is compared with the filter.
"""
from .config import MODE_TEST
from .errors import PackageNotFoundError
from .maven import MavenRepository
from .pom import SEPARATOR, parse_coordinate
from .test_repo import load_test_repo


class MavenSource:
    """Dependencies of Maven packages; nodes are ``group:artifact:version``."""

    def __init__(self, repository):
        """Wrap a MavenRepository."""
        self.repository = repository

    def dependencies(self, node):
        """Return the direct dependencies of the package."""
        found = self.repository.direct_dependencies(parse_coordinate(node))
        return [str(item) for item in found]

    def package_name(self, node):
        """Return ``group:artifact`` without the version."""
        return node.rsplit(SEPARATOR, 1)[0]

    @property
    def warnings(self):
        """Return the warnings collected while reading the repository."""
        return self.repository.warnings


class GraphFileSource:
    """Dependencies from a test repository; nodes are capital letters."""

    def __init__(self, packages):
        """Create a source from {package: [dependencies]}."""
        self.packages = packages
        self.warnings = []

    def dependencies(self, node):
        """Return the dependencies; unknown packages have none."""
        return list(self.packages.get(node, []))

    def package_name(self, node):
        """Return the name of the package (the node itself)."""
        return node


def open_source(config):
    """Return (source, root node) for the configured repository."""
    if config.mode == MODE_TEST:
        packages = load_test_repo(config.repo)
        if config.package not in packages:
            raise PackageNotFoundError(
                f"package {config.package} is not described in {config.repo}")
        return GraphFileSource(packages), config.package
    return MavenSource(MavenRepository(config.repo)), config.package

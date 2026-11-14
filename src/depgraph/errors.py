"""Exceptions of the tool; their messages are shown to the user."""


class DepGraphError(Exception):
    """Base class of all expected errors."""

    exit_code = 1


class ConfigError(DepGraphError):
    """A command-line parameter is missing or invalid."""

    exit_code = 2


class RepositoryError(DepGraphError):
    """A repository cannot be read or contains invalid data."""


class PackageNotFoundError(RepositoryError):
    """The requested package does not exist in the repository."""


class OutputError(DepGraphError):
    """The image of the graph cannot be produced or saved."""

    exit_code = 3

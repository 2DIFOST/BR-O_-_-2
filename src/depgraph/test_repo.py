"""Test repository: a text file that describes a graph of packages.

Every line has the form ``A: B C`` — package A depends on B and C.
Package names consist of capital Latin letters. Empty lines and text
after ``#`` are ignored. A package that is mentioned only as a dependency
has no dependencies of its own.
"""
import re

from .errors import RepositoryError

NAME = re.compile(r"[A-Z]+")
SEPARATOR = ":"
COMMENT = "#"


def parse_line(text, number, source):
    """Parse one non-empty line; return (package, dependencies)."""
    name, separator, rest = text.partition(SEPARATOR)
    name = name.strip()
    where = f"{source}, line {number}"
    if not separator:
        raise RepositoryError(f"{where}: expected 'A: B C', got '{text}'")
    if not NAME.fullmatch(name):
        raise RepositoryError(
            f"{where}: invalid package name '{name}' (use A-Z)")
    dependencies = []
    for item in rest.split():
        if not NAME.fullmatch(item):
            raise RepositoryError(
                f"{where}: invalid dependency name '{item}' (use A-Z)")
        if item not in dependencies:
            dependencies.append(item)
    return name, dependencies


def parse_test_repo(text, source="test repository"):
    """Parse the text of a test repository into {package: [dependencies]}."""
    packages = {}
    for number, line in enumerate(text.splitlines(), start=1):
        content = line.split(COMMENT, 1)[0].strip()
        if not content:
            continue
        name, dependencies = parse_line(content, number, source)
        if name in packages:
            raise RepositoryError(
                f"{source}, line {number}: package {name} is described twice")
        packages[name] = dependencies
    return packages


def load_test_repo(path):
    """Read and parse a test repository file."""
    try:
        with open(path, encoding="utf-8-sig") as file:
            text = file.read()
    except UnicodeDecodeError as error:
        raise RepositoryError(f"{path} is not a UTF-8 text file") from error
    except OSError as error:
        raise RepositoryError(f"cannot read {path}: {error}") from error
    return parse_test_repo(text, path)

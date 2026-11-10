"""Parsing of Maven POM files (only the parts needed for dependencies)."""
from dataclasses import dataclass, field
from xml.etree import ElementTree as xml_tree

from .errors import RepositoryError

SEPARATOR = ":"
COORDINATE_PARTS = 3
ROOT_TAG = "project"


@dataclass(frozen=True)
class Coordinate:
    """Identity of a package version: group, artifact and version."""

    group_id: str
    artifact_id: str
    version: str

    @property
    def name(self):
        """Return the package name without the version."""
        return f"{self.group_id}{SEPARATOR}{self.artifact_id}"

    def __str__(self):
        """Return the text form ``groupId:artifactId:version``."""
        return f"{self.name}{SEPARATOR}{self.version}"


def parse_coordinate(text):
    """Build a Coordinate from ``groupId:artifactId:version``."""
    parts = text.split(SEPARATOR)
    if len(parts) != COORDINATE_PARTS:
        raise RepositoryError(f"invalid package coordinate '{text}'")
    return Coordinate(*parts)


@dataclass(frozen=True)
class RawDependency:
    """A dependency exactly as written in a POM (values may be unset)."""

    group_id: str
    artifact_id: str
    version: str | None = None
    scope: str | None = None
    optional: bool = False
    dep_type: str | None = None


@dataclass
class Pom:
    """The content of one POM file that matters for dependencies."""

    artifact_id: str
    parent: Coordinate | None = None
    properties: dict = field(default_factory=dict)
    dependencies: list = field(default_factory=list)
    managed: list = field(default_factory=list)


def child_text(element, name):
    """Return the stripped text of the child element or None."""
    child = element.find(name)
    if child is None or not child.text:
        return None
    return child.text.strip() or None


def strip_namespaces(root):
    """Remove XML namespaces from all tags of the tree."""
    for element in root.iter():
        if isinstance(element.tag, str):
            element.tag = element.tag.rpartition("}")[2]


def parse_dependency(element, source):
    """Convert a <dependency> element to RawDependency."""
    group_id = child_text(element, "groupId")
    artifact_id = child_text(element, "artifactId")
    if group_id is None or artifact_id is None:
        raise RepositoryError(
            f"invalid POM {source}: dependency without groupId or artifactId")
    optional = (child_text(element, "optional") or "").lower() == "true"
    return RawDependency(
        group_id, artifact_id, child_text(element, "version"),
        child_text(element, "scope"), optional, child_text(element, "type"))


def parse_dependencies(container, source):
    """Parse all dependencies of a <dependencies> element (may be None)."""
    if container is None:
        return []
    return [parse_dependency(item, source)
            for item in container.findall("dependency")]


def parse_parent(root, source):
    """Return the Coordinate of the parent POM or None."""
    parent = root.find("parent")
    if parent is None:
        return None
    parts = [child_text(parent, name)
             for name in ("groupId", "artifactId", "version")]
    if None in parts:
        raise RepositoryError(f"invalid POM {source}: incomplete <parent>")
    return Coordinate(*parts)


def parse_properties(root):
    """Return the <properties> of the POM as a dictionary."""
    container = root.find("properties")
    if container is None:
        return {}
    return {item.tag: (item.text or "").strip()
            for item in container if isinstance(item.tag, str)}


def parse_pom(data, source):
    """Parse the bytes of a POM file; ``source`` is used in messages."""
    try:
        root = xml_tree.fromstring(data)
    except xml_tree.ParseError as error:
        raise RepositoryError(f"invalid POM {source}: {error}") from error
    strip_namespaces(root)
    if root.tag != ROOT_TAG:
        raise RepositoryError(
            f"invalid POM {source}: root element must be <{ROOT_TAG}>")
    artifact_id = child_text(root, "artifactId")
    if artifact_id is None:
        raise RepositoryError(f"invalid POM {source}: no artifactId")
    management = root.find("dependencyManagement")
    managed = None if management is None else management.find("dependencies")
    return Pom(
        artifact_id=artifact_id,
        parent=parse_parent(root, source),
        properties=parse_properties(root),
        dependencies=parse_dependencies(root.find("dependencies"), source),
        managed=parse_dependencies(managed, source),
    )

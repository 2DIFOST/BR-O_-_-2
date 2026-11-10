"""Direct dependencies of a Maven package read from POM files."""
import re

from .errors import PackageNotFoundError, RepositoryError
from .fetch import fetch_bytes
from .pom import Coordinate, parse_pom

FOLLOWED_SCOPES = (None, "compile", "runtime")
UNRESOLVED_VERSIONS = ("RELEASE", "LATEST")
MAX_PARENTS = 20
MAX_IMPORT_DEPTH = 5
MAX_PASSES = 10
PLACEHOLDER = re.compile(r"\$\{([^}]+)\}")
RANGE_BRACKETS = "[]()"


def interpolate(text, properties):
    """Replace ``${name}`` placeholders using the properties."""
    for _ in range(MAX_PASSES):
        result = PLACEHOLDER.sub(
            lambda match: properties.get(match.group(1), match.group(0)),
            text)
        if result == text:
            break
        text = result
    return text


def normalize_version(version):
    """Return a concrete version or None if it cannot be determined.

    A version range such as ``[1.0,2.0)`` is replaced by its lower bound.
    """
    if not version or "${" in version or version in UNRESOLVED_VERSIONS:
        return None
    if version[0] not in RANGE_BRACKETS:
        return version
    text = version.strip(RANGE_BRACKETS)
    bounds = [part.strip() for part in text.split(",")]
    return next((part for part in bounds if part), None)


def builtin_properties(coordinate, pom):
    """Return the ``project.*`` properties of the package."""
    values = {
        "version": coordinate.version,
        "groupId": coordinate.group_id,
        "artifactId": coordinate.artifact_id,
    }
    properties = {}
    for key, value in values.items():
        properties[key] = value
        properties[f"project.{key}"] = value
        properties[f"pom.{key}"] = value
    if pom.parent is not None:
        parent = {
            "version": pom.parent.version,
            "groupId": pom.parent.group_id,
            "artifactId": pom.parent.artifact_id,
        }
        for key, value in parent.items():
            properties[f"parent.{key}"] = value
            properties[f"project.parent.{key}"] = value
    return properties


def managed_entry(raw, properties):
    """Return ``(group, artifact, version)`` of a managed dependency.

    Returns None if the version cannot be determined.
    """
    version = normalize_version(interpolate(raw.version or "", properties))
    if version is None:
        return None
    return (interpolate(raw.group_id, properties),
            interpolate(raw.artifact_id, properties), version)


def is_followed(raw):
    """Return True if the dependency is part of the dependency graph.

    Only compile and runtime dependencies that are not optional count.
    """
    return raw.scope in FOLLOWED_SCOPES and not raw.optional


def own_and_inherited(poms):
    """Return the dependencies of a POM chain, own ones first.

    A dependency declared in a child hides the same one from a parent.
    """
    result = []
    keys = set()
    for pom in poms:
        for raw in pom.dependencies:
            key = (raw.group_id, raw.artifact_id, raw.dep_type)
            if key not in keys:
                keys.add(key)
                result.append(raw)
    return result


class MavenRepository:
    """A Maven repository that is read through its base URL."""

    def __init__(self, base_url, fetch=fetch_bytes):
        """Create a repository; ``fetch`` downloads a URL as bytes."""
        self.base_url = base_url.rstrip("/")
        self.fetch = fetch
        self.warnings = []
        self.poms = {}
        self.managed_cache = {}

    def pom_url(self, coordinate):
        """Return the URL of the POM file of the package."""
        group_path = coordinate.group_id.replace(".", "/")
        artifact = coordinate.artifact_id
        name = f"{artifact}-{coordinate.version}.pom"
        return (f"{self.base_url}/{group_path}/{artifact}/"
                f"{coordinate.version}/{name}")

    def load_pom(self, coordinate):
        """Download and parse the POM of the package (with a cache)."""
        if coordinate not in self.poms:
            url = self.pom_url(coordinate)
            self.poms[coordinate] = parse_pom(self.fetch(url), url)
        return self.poms[coordinate]

    def chain(self, coordinate):
        """Return the POMs of the package and its parents, child first."""
        poms = []
        seen = set()
        current = coordinate
        while current is not None:
            if current in seen or len(poms) >= MAX_PARENTS:
                raise RepositoryError(
                    f"parent POM chain of {coordinate} is cyclic or too long")
            seen.add(current)
            try:
                poms.append(self.load_pom(current))
            except PackageNotFoundError:
                if not poms:
                    raise
                raise RepositoryError(
                    f"parent POM {current} of {coordinate} not found"
                ) from None
            current = poms[-1].parent
        return poms

    def properties(self, coordinate, poms):
        """Return all properties visible in the POM of the package."""
        properties = {}
        for pom in reversed(poms):
            properties.update(pom.properties)
        properties.update(builtin_properties(coordinate, poms[0]))
        return properties

    def managed_versions(self, coordinate, depth=0):
        """Return versions from dependencyManagement, including BOMs.

        The result maps ``(groupId, artifactId)`` to a version.
        """
        if coordinate not in self.managed_cache:
            poms = self.chain(coordinate)
            properties = self.properties(coordinate, poms)
            self.managed_cache[coordinate] = self.collect_managed(
                poms, properties, depth)
        return self.managed_cache[coordinate]

    def collect_managed(self, poms, properties, depth):
        """Collect managed versions of a POM chain; child entries win."""
        managed = {}
        boms = []
        for pom in poms:
            for raw in pom.managed:
                entry = managed_entry(raw, properties)
                if entry is None:
                    continue
                if raw.scope == "import" and raw.dep_type == "pom":
                    boms.append(Coordinate(*entry))
                else:
                    managed.setdefault(entry[:2], entry[2])
        for bom in boms:
            for key, version in self.imported_versions(bom, depth).items():
                managed.setdefault(key, version)
        return managed

    def imported_versions(self, bom, depth):
        """Return the managed versions of an imported BOM (or nothing)."""
        if depth >= MAX_IMPORT_DEPTH:
            self.warnings.append(f"BOM {bom}: imports are nested too deeply")
            return {}
        try:
            return self.managed_versions(bom, depth + 1)
        except RepositoryError as error:
            self.warnings.append(f"BOM {bom} ignored: {error}")
            return {}

    def resolve(self, raw, properties, managed, owner):
        """Turn a raw dependency into a Coordinate or None if unresolved."""
        group = interpolate(raw.group_id, properties)
        artifact = interpolate(raw.artifact_id, properties)
        version = raw.version or managed.get((group, artifact))
        version = normalize_version(interpolate(version or "", properties))
        if version is None:
            self.warnings.append(
                f"{owner}: no version for {group}:{artifact}, skipped")
            return None
        return Coordinate(group, artifact, version)

    def direct_dependencies(self, coordinate):
        """Return the direct dependencies of the package as Coordinates.

        Raises PackageNotFoundError if the POM of the package is missing.
        """
        poms = self.chain(coordinate)
        properties = self.properties(coordinate, poms)
        managed = self.managed_versions(coordinate)
        result = []
        for raw in own_and_inherited(poms):
            if not is_followed(raw):
                continue
            found = self.resolve(raw, properties, managed, coordinate)
            if found is not None and found not in result:
                result.append(found)
        return result

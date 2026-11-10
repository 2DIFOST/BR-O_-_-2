"""Tests of the extraction of direct dependencies (stage 2)."""
import os
import unittest

from depgraph.errors import PackageNotFoundError, RepositoryError
from depgraph.maven import (
    MavenRepository, interpolate, normalize_version,
)
from depgraph.pom import parse_coordinate
from helpers import EXAMPLES_DIR, file_url, make_temp_dir, write_file

FIXTURE = os.path.join(EXAMPLES_DIR, "maven-repo")


def fixture_repository():
    """Return a repository that reads the example POM files."""
    return MavenRepository(file_url(FIXTURE))


def names(repository, text):
    """Return direct dependencies of the package as text."""
    coordinate = parse_coordinate(text)
    return [str(item) for item in repository.direct_dependencies(coordinate)]


class HelpersTest(unittest.TestCase):
    """Properties and versions."""

    def test_interpolate(self):
        self.assertEqual(interpolate("${a}-${b}", {"a": "1", "b": "2"}), "1-2")

    def test_interpolate_nested(self):
        self.assertEqual(interpolate("${a}", {"a": "${b}", "b": "x"}), "x")

    def test_unknown_property_stays(self):
        self.assertEqual(interpolate("${zzz}", {}), "${zzz}")

    def test_cyclic_properties_terminate(self):
        self.assertIn("${", interpolate("${a}", {"a": "${b}", "b": "${a}"}))

    def test_versions(self):
        self.assertEqual(normalize_version("1.2"), "1.2")
        self.assertEqual(normalize_version("[1.0,2.0)"), "1.0")
        self.assertEqual(normalize_version("(,2.0]"), "2.0")
        self.assertEqual(normalize_version("[1.5]"), "1.5")
        self.assertIsNone(normalize_version("${x}"))
        self.assertIsNone(normalize_version("RELEASE"))
        self.assertIsNone(normalize_version(None))


class DirectDependenciesTest(unittest.TestCase):
    """Reading of dependencies from the example repository."""

    def test_parent_management_and_inheritance(self):
        repository = fixture_repository()
        self.assertEqual(names(repository, "org.example:shop-app:1.0.0"), [
            "org.example:shop-web:1.0.0",
            "org.example:shop-db:1.0.0",
            "org.example:ghost:9.9.9",
            "org.example:logging-api:1.0.0",
        ])

    def test_version_from_an_imported_bom(self):
        repository = fixture_repository()
        self.assertIn(
            "org.example:json-lib:4.0.0",
            names(repository, "org.example:shop-web:1.0.0"))

    def test_test_and_optional_dependencies_are_skipped(self):
        repository = fixture_repository()
        result = names(repository, "org.example:shop-app:1.0.0")
        self.assertNotIn("org.example:test-kit:1.0.0", result)
        self.assertNotIn("org.example:code-gen:1.0.0", result)

    def test_runtime_dependency_is_kept(self):
        repository = fixture_repository()
        self.assertIn(
            "org.example:pool-lib:2.0.0",
            names(repository, "org.example:shop-db:1.0.0"))

    def test_project_version_and_range(self):
        repository = fixture_repository()
        self.assertEqual(names(repository, "org.example:report-core:3.1.0"), [
            "org.example:report-render:3.1.0",
            "org.example:range-lib:1.0",
        ])

    def test_property_that_uses_project_version(self):
        repository = fixture_repository()
        self.assertEqual(names(repository, "org.example:report-tool:3.1.0"), [
            "org.example:report-core:3.1.0",
            "org.example:common-utils:1.2.0",
        ])

    def test_missing_root_package(self):
        repository = fixture_repository()
        with self.assertRaises(PackageNotFoundError):
            names(repository, "org.example:nope:1.0")

    def test_pom_is_downloaded_once(self):
        calls = []

        def fetch(url):
            calls.append(url)
            return b"<project><artifactId>a</artifactId></project>"

        repository = MavenRepository("https://repo.test", fetch)
        coordinate = parse_coordinate("g:a:1")
        repository.direct_dependencies(coordinate)
        repository.direct_dependencies(coordinate)
        self.assertEqual(calls, ["https://repo.test/g/a/1/a-1.pom"])


class BrokenRepositoryTest(unittest.TestCase):
    """Problems inside a repository."""

    def repository(self, files):
        """Create a file repository from {relative path: text}."""
        root = make_temp_dir(self)
        for relative, text in files.items():
            directory = os.path.join(root, os.path.dirname(relative))
            os.makedirs(directory, exist_ok=True)
            write_file(directory, os.path.basename(relative), text)
        return MavenRepository(file_url(root))

    def test_invalid_xml(self):
        repository = self.repository({"g/a/1/a-1.pom": "<project>"})
        with self.assertRaisesRegex(RepositoryError, "invalid POM"):
            names(repository, "g:a:1")

    def test_missing_parent(self):
        pom = ("<project><parent><groupId>g</groupId><artifactId>p"
               "</artifactId><version>1</version></parent>"
               "<artifactId>a</artifactId></project>")
        repository = self.repository({"g/a/1/a-1.pom": pom})
        with self.assertRaisesRegex(RepositoryError, "parent POM"):
            names(repository, "g:a:1")

    def test_parent_cycle(self):
        pom = ("<project><parent><groupId>g</groupId><artifactId>a"
               "</artifactId><version>1</version></parent>"
               "<artifactId>a</artifactId></project>")
        repository = self.repository({"g/a/1/a-1.pom": pom})
        with self.assertRaisesRegex(RepositoryError, "cyclic"):
            names(repository, "g:a:1")

    def test_dependency_without_version_is_skipped_with_warning(self):
        pom = ("<project><artifactId>a</artifactId><dependencies>"
               "<dependency><groupId>g</groupId><artifactId>b</artifactId>"
               "</dependency></dependencies></project>")
        repository = self.repository({"g/a/1/a-1.pom": pom})
        self.assertEqual(names(repository, "g:a:1"), [])
        self.assertIn("no version for g:b", repository.warnings[0])


if __name__ == "__main__":
    unittest.main()

"""Tests of the POM parser (stage 2)."""
import unittest

from depgraph.errors import RepositoryError
from depgraph.pom import Coordinate, parse_coordinate, parse_pom

POM = b"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>g</groupId><artifactId>p</artifactId><version>2</version>
  </parent>
  <artifactId>app</artifactId>
  <!-- a comment -->
  <properties><lib.version>1.5</lib.version><!-- c --></properties>
  <dependencyManagement><dependencies>
    <dependency><groupId>g</groupId><artifactId>m</artifactId>
      <version>3</version></dependency>
  </dependencies></dependencyManagement>
  <dependencies>
    <dependency><groupId>g</groupId><artifactId>a</artifactId>
      <version>${lib.version}</version><scope>runtime</scope></dependency>
    <dependency><groupId>g</groupId><artifactId>b</artifactId>
      <optional>true</optional></dependency>
  </dependencies>
</project>
"""


class PomTest(unittest.TestCase):
    """Reading of the parts of a POM."""

    def test_namespaced_pom_is_parsed(self):
        pom = parse_pom(POM, "test")
        self.assertEqual(pom.artifact_id, "app")
        self.assertEqual(pom.parent, Coordinate("g", "p", "2"))
        self.assertEqual(pom.properties, {"lib.version": "1.5"})

    def test_dependencies(self):
        pom = parse_pom(POM, "test")
        first, second = pom.dependencies
        self.assertEqual(first.version, "${lib.version}")
        self.assertEqual(first.scope, "runtime")
        self.assertFalse(first.optional)
        self.assertIsNone(second.version)
        self.assertTrue(second.optional)

    def test_dependency_management(self):
        pom = parse_pom(POM, "test")
        self.assertEqual([item.artifact_id for item in pom.managed], ["m"])

    def test_pom_without_namespace(self):
        pom = parse_pom(b"<project><artifactId>x</artifactId></project>", "t")
        self.assertEqual(pom.dependencies, [])

    def test_not_xml(self):
        with self.assertRaisesRegex(RepositoryError, "invalid POM"):
            parse_pom(b"this is not xml", "t")

    def test_wrong_root_element(self):
        with self.assertRaisesRegex(RepositoryError, "root element"):
            parse_pom(b"<other/>", "t")

    def test_missing_artifact_id(self):
        with self.assertRaisesRegex(RepositoryError, "no artifactId"):
            parse_pom(b"<project/>", "t")

    def test_dependency_without_artifact_id(self):
        data = (b"<project><artifactId>x</artifactId><dependencies>"
                b"<dependency><groupId>g</groupId></dependency>"
                b"</dependencies></project>")
        with self.assertRaisesRegex(RepositoryError, "without groupId"):
            parse_pom(data, "t")

    def test_incomplete_parent(self):
        data = (b"<project><parent><groupId>g</groupId></parent>"
                b"<artifactId>x</artifactId></project>")
        with self.assertRaisesRegex(RepositoryError, "incomplete"):
            parse_pom(data, "t")


class CoordinateTest(unittest.TestCase):
    """Coordinates of packages."""

    def test_text_form(self):
        coordinate = parse_coordinate("org.example:app:1.0")
        self.assertEqual(str(coordinate), "org.example:app:1.0")
        self.assertEqual(coordinate.name, "org.example:app")

    def test_invalid_text(self):
        with self.assertRaises(RepositoryError):
            parse_coordinate("org.example:app")


if __name__ == "__main__":
    unittest.main()

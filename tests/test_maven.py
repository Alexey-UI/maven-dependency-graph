"""Offline tests for XML parsing and HTTP repository interpretation."""

import unittest
from unittest.mock import patch
from urllib.error import URLError

from dependency_graph.maven import MavenRepository, fetch_pom
from dependency_graph.model import Package
from dependency_graph.pom import expand, parse_xml


class MavenTests(unittest.TestCase):
    """Resolve fixture POMs without network or a package manager."""

    def setUp(self):
        """Prepare a versioned package and an injected fetch function."""
        self.package = Package("org.demo:root", "1.0")
        self.content = b"<project/>"
        self.urls = []
        self.repo = MavenRepository("https://repo.test", self.fetch)

    def fetch(self, url):
        """Record repository requests and return fixture bytes."""
        self.urls.append(url)
        return self.content

    def test_url_and_cache(self):
        """Use the requested version and cache parsed POMs."""
        self.assertEqual(self.repo.dependencies(self.package), [])
        self.repo.dependencies(self.package)
        self.assertEqual(self.urls, [
            "https://repo.test/org/demo/root/1.0/root-1.0.pom"
        ])

    def test_properties_scopes_and_plugins(self):
        """Read project dependencies, expand versions and omit test scope."""
        self.content = b'''<project xmlns="http://maven.apache.org/POM/4.0.0">
          <properties><v>2.0</v></properties>
          <dependencies>
            <dependency><groupId>g</groupId><artifactId>a</artifactId>
              <version>${v}</version></dependency>
            <dependency><groupId>g</groupId><artifactId>b</artifactId>
              <version>1</version><scope>test</scope></dependency>
            <dependency><groupId>g</groupId><artifactId>c</artifactId>
              <version>1</version><optional>true</optional></dependency>
          </dependencies>
          <build><plugins><plugin><dependencies><dependency/>
          </dependencies></plugin></plugins></build></project>'''
        self.assertEqual(self.repo.dependencies(self.package),
                         [Package("g:a", "2.0")])

    def test_parent_management(self):
        """Inherit managed versions and resolve child property references."""
        parent = b'''<project><properties><v>2</v></properties>
        <dependencyManagement><dependencies><dependency>
        <groupId>g</groupId><artifactId>a</artifactId><version>${v}</version>
        </dependency></dependencies></dependencyManagement></project>'''
        child = b'''<project><parent><groupId>g</groupId>
        <artifactId>p</artifactId>
        <version>1</version></parent><dependencies><dependency>
        <groupId>g</groupId><artifactId>a</artifactId>
        </dependency></dependencies></project>'''
        repo = MavenRepository("https://repo", lambda url:
                               parent if "/p/" in url else child)
        self.assertEqual(repo.dependencies(self.package), [Package("g:a", "2")])

    def test_bad_xml_properties_and_version(self):
        """Reject malformed XML, property cycles and missing versions."""
        for content in (b"<", b"<html/>"):
            with self.assertRaises(ValueError):
                parse_xml(content)
        for value in ("${missing}", "${a}"):
            with self.assertRaises(ValueError):
                expand(value, {"a": "${b}", "b": "${a}"})
        with self.assertRaises(ValueError):
            Package("g:a", "[1,2)")

    def test_network_error(self):
        """Wrap transport errors as user-facing failures."""
        with patch("dependency_graph.maven.urlopen", side_effect=URLError("x")):
            with self.assertRaisesRegex(ValueError, "Не удалось загрузить"):
                fetch_pom("https://repo/x.pom")

    def test_imported_bom(self):
        """Use a BOM-managed version for an unversioned dependency."""
        bom = b'''<project><dependencyManagement><dependencies><dependency>
        <groupId>g</groupId><artifactId>a</artifactId><version>2</version>
        </dependency></dependencies></dependencyManagement></project>'''
        child = b'''<project><dependencyManagement><dependencies><dependency>
        <groupId>g</groupId><artifactId>bom</artifactId><version>1</version>
        <type>pom</type><scope>import</scope></dependency>
        </dependencies></dependencyManagement><dependencies><dependency>
        <groupId>g</groupId><artifactId>a</artifactId>
        </dependency></dependencies></project>'''
        repo = MavenRepository("https://repo", lambda url:
                               bom if "/bom/" in url else child)
        self.assertEqual(repo.dependencies(self.package), [Package("g:a", "2")])

    def test_parent_cycle(self):
        """Reject a cyclic parent model instead of recurring forever."""
        self.content = b'''<project><parent><groupId>org.demo</groupId>
        <artifactId>root</artifactId><version>1.0</version>
        </parent></project>'''
        with self.assertRaisesRegex(ValueError, "Цикл наследования"):
            self.repo.dependencies(self.package)

    def test_unsupported_dependency_and_missing_version(self):
        """Unsupported Maven features fail explicitly, not silently."""
        for extra in ("", "<version>1</version><classifier>tests</classifier>",
                      "<version>1</version><type>war</type>",
                      "<version>1</version><exclusions><exclusion>"
                      "<groupId>g</groupId><artifactId>b</artifactId>"
                      "</exclusion></exclusions>"):
            with self.subTest(extra=extra):
                self.repo.cache.clear()
                self.content = ("<project><dependencies><dependency>"
                                "<groupId>g</groupId><artifactId>a</artifactId>"
                                + extra + "</dependency></dependencies>"
                                "</project>").encode()
                with self.assertRaises(ValueError):
                    self.repo.dependencies(self.package)

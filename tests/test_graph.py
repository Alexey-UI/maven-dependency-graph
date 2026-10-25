"""Graph depth, filtering, cycle and iterative traversal regressions."""

from pathlib import Path
import tempfile
import unittest

from dependency_graph.graph import build_graph
from dependency_graph.model import Package
from dependency_graph.test_repository import TestRepository

EXAMPLES = Path(__file__).resolve().parents[1] / "examples/repositories"
CHAIN_LENGTH = 1500


def package(name):
    """Return a test node with the fixture version."""
    return Package(name, "1")


class GraphTests(unittest.TestCase):
    """Check selected subgraphs and avoid recursion limits."""

    def graph(self, name, depth=10, substring=""):
        """Build a fixture graph with configurable analysis limits."""
        repo = TestRepository(EXAMPLES / f"{name}.yaml")
        return build_graph(repo, package("A"), depth, substring)

    def test_depth_boundary(self):
        """Depth zero includes only the root, one only direct edges."""
        self.assertEqual(self.graph("chain", 0), {package("A"): []})
        graph = self.graph("chain", 1)
        self.assertEqual(set(graph), {package("A"), package("B")})
        self.assertEqual(graph[package("B")], [])

    def test_cycle_and_diamond(self):
        """Cycles keep their edges; shared nodes are represented once."""
        graph = self.graph("cycle")
        self.assertIn(package("A"), graph[package("C")])
        self.assertEqual(set(self.graph("diamond")),
                         {package(name) for name in "ABCD"})

    def test_filter_stops_traversal(self):
        """An excluded chain node and its descendants are not visited."""
        graph = self.graph("chain", substring="B")
        self.assertEqual(graph, {package("A"): []})
        with self.assertRaisesRegex(ValueError, "Корневой"):
            self.graph("chain", substring="A")

    def test_shorter_path_reexpands_node(self):
        """A later shorter path must expose dependencies within the limit."""
        graph = self.graph("shorter", 3)
        self.assertEqual(graph[package("E")], [package("F")])

    def test_deep_graph_without_recursion(self):
        """A chain beyond Python's recursion limit is traversed safely."""
        class Chain:
            """Generate uppercase names and one successor at a time."""

            def dependencies(self, node):
                """Grow the name until the fixture length is reached."""
                if len(node.name) >= CHAIN_LENGTH:
                    return []
                return [package(node.name + "A")]

        graph = build_graph(Chain(), package("A"), CHAIN_LENGTH)
        self.assertEqual(len(graph), CHAIN_LENGTH)

    def test_malformed_repository(self):
        """Reject unknown targets, bad types, duplicates and invalid names."""
        cases = ("[]", "A: [B]", "a: []", "A: 2", "A: [A, A]",
                 "A: [1]", "{}", "A: []\nA: []")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "repo.yaml"
            for content in cases:
                with self.subTest(content=content):
                    path.write_text(content)
                    with self.assertRaises(ValueError):
                        TestRepository(path)

    def test_missing_root(self):
        """Unknown requested package produces an explicit error."""
        repo = TestRepository(EXAMPLES / "single.yaml")
        with self.assertRaisesRegex(ValueError, "Пакет не найден"):
            repo.dependencies(package("Z"))

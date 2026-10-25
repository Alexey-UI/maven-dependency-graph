"""Dependency-first ordering and cycle diagnostics."""

import unittest

from dependency_graph.order import load_order


class OrderTests(unittest.TestCase):
    """Verify precedence, uniqueness, determinism and cycle failures."""

    def test_chain_diamond_single(self):
        """Leaves precede dependants and a shared dependency appears once."""
        self.assertEqual(load_order({"A": []}, "A"), ["A"])
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        self.assertEqual(load_order(graph, "A"), ["D", "B", "C", "A"])
        self.assertEqual(load_order({"A": ["B"], "B": []}, "A"), ["B", "A"])

    def test_cycles(self):
        """No total dependency-first order exists for a directed cycle."""
        for graph in ({"A": ["A"]}, {"A": ["B"], "B": ["A"]}):
            with self.subTest(graph=graph):
                with self.assertRaisesRegex(ValueError, "Цикл:"):
                    load_order(graph, "A")

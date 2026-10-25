"""Diagram output, iterative tree rendering and renderer failure tests."""

from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

from dependency_graph.model import Package
from dependency_graph.visualize import ascii_tree, mermaid_text
from dependency_graph.visualize import render_png, save_visualization


class VisualizationTests(unittest.TestCase):
    """Validate text structure independently of external browser software."""

    def test_mermaid_all_nodes_and_edges(self):
        """Safe IDs preserve isolated nodes and cyclic edges."""
        root = Package("org.demo:end", "1")
        other = Package("org.demo:a", "2")
        graph = {root: [other], other: [root]}
        self.assertEqual(mermaid_text(graph),
                         'flowchart TD\n    n0["org.demo:end:1"]\n'
                         '    n1["org.demo:a:2"]\n'
                         '    n0 --> n1\n    n1 --> n0\n')

    def test_ascii_cycle_and_shared_nodes(self):
        """Mark back edges as cycles and repeated subtrees as shared."""
        graph = {"A": ["B", "C"], "B": ["D"],
                 "C": ["D"], "D": ["A"]}
        result = ascii_tree(graph, "A")
        self.assertIn("A [cycle]", result)
        self.assertIn("D [shared]", result)
        self.assertIn("|-- B", result)
        self.assertIn("\\-- C", result)
        self.assertEqual(ascii_tree({"A": []}, "A"), "A")

    def test_missing_renderer(self):
        """Missing mmdc produces an installation hint."""
        with patch("dependency_graph.visualize.shutil.which",
                   return_value=None):
            with self.assertRaisesRegex(ValueError, "mmdc не найден"):
                render_png("graph.mmd", "graph.png")

    def test_mermaid_sidecar_and_error(self):
        """Keep textual Mermaid source even when rendering fails."""
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "graph.png"
            with patch("dependency_graph.visualize.render_png",
                       side_effect=OSError("renderer failed")):
                with self.assertRaisesRegex(ValueError, "renderer failed"):
                    save_visualization({"A": []}, output)
            self.assertIn('n0["A"]', output.with_suffix(".mmd").read_text())

    def test_failed_renderer_preserves_existing_png(self):
        """A failed browser must not replace the previous successful image."""
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "graph.png"
            output.write_bytes(b"previous-image")
            failure = subprocess.CompletedProcess([], 1, "", "browser failed")
            with patch("dependency_graph.visualize.shutil.which",
                       return_value="mmdc"), patch(
                           "dependency_graph.visualize.subprocess.run",
                           return_value=failure):
                with self.assertRaisesRegex(ValueError, "browser failed"):
                    render_png("graph.mmd", output)
            self.assertEqual(output.read_bytes(), b"previous-image")

"""Optional end-to-end checks with a real Mermaid CLI and browser."""

from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
import struct
import tempfile
import unittest

import yaml

from dependency_graph.__main__ import main
from dependency_graph.visualize import PNG_SIGNATURE

PNG_HEADER_LENGTH = 24


@unittest.skipUnless(os.environ.get("RUN_RENDER_TESTS") == "1",
                     "Для реального Chrome задайте RUN_RENDER_TESTS=1")
class RenderIntegrationTests(unittest.TestCase):
    """Exercise the full CLI, filesystem outputs and ASCII switch."""

    def test_real_png_and_ascii_switch(self):
        """Create real cyclic diagrams with and without terminal trees."""
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            (base / "repo.yaml").write_text("A: [B]\nB: [A]\n")
            config = {"package": "A", "repository": "repo.yaml",
                      "test_mode": True, "version": "1",
                      "output": "graph.png", "ascii_tree": True,
                      "max_depth": 10, "filter_substring": ""}
            for enabled in (True, False):
                config["ascii_tree"] = enabled
                path = base / "config.yaml"
                path.write_text(yaml.safe_dump(config))
                output = StringIO()
                with redirect_stdout(output):
                    self.assertEqual(main([str(path)]), 0)
                self.assertEqual("[cycle]" in output.getvalue(), enabled)
                content = (base / "graph.png").read_bytes()
                header = content[:PNG_HEADER_LENGTH]
                self.assertTrue(header.startswith(PNG_SIGNATURE))
                width, height = struct.unpack(">II", header[16:])
                self.assertTrue(width and height)
                self.assertIn("n1 --> n0", (base / "graph.mmd").read_text())

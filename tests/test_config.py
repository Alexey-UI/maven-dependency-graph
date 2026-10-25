"""Configuration type, value, filesystem and CLI error coverage."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest

import yaml

from dependency_graph.__main__ import main
from dependency_graph.config import load_config


class ConfigTests(unittest.TestCase):
    """Exercise every configurable field and malformed documents."""

    def setUp(self):
        """Prepare an isolated valid configuration."""
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "config.yaml"
        self.data = {
            "package": "junit:junit", "version": "4.13.2",
            "repository": "https://repo.maven.apache.org/maven2",
            "test_mode": False, "output": "graph.png",
            "ascii_tree": True, "max_depth": 3, "filter_substring": "",
        }

    def write(self):
        """Serialize the current test settings."""
        self.path.write_text(yaml.safe_dump(self.data), encoding="utf-8")

    def test_valid_and_relative_output(self):
        """Valid configuration resolves output beside its YAML file."""
        self.write()
        config = load_config(self.path)
        expected = self.path.parent.resolve() / "graph.png"
        self.assertEqual(config.output, str(expected))

    def test_invalid_values(self):
        """Each field rejects invalid values, including bool-as-int."""
        invalid = {
            "package": ["", "bad/name", "x:y:z", None],
            "repository": ["", "ftp://host", "https://h/?x=y"],
            "test_mode": ["false", 1, None],
            "version": ["", "../x", "[1,2)", 3],
            "output": ["", "result.svg", None],
            "ascii_tree": ["true", 1, None],
            "max_depth": [-1, True, "2", 1.5],
            "filter_substring": [None, 2, []],
        }
        for key, values in invalid.items():
            original = self.data[key]
            for value in values:
                with self.subTest(key=key, value=value):
                    self.data[key] = value
                    self.write()
                    with self.assertRaises(ValueError):
                        load_config(self.path)
            self.data[key] = original

    def test_yaml_and_key_errors(self):
        """Missing, extra, duplicate keys and invalid YAML fail clearly."""
        self.write()
        valid = self.path.read_text()
        for content in ("[", "[]", valid + "package: other\n", "x: 1"):
            with self.subTest(content=content):
                self.path.write_text(content)
                with self.assertRaises(ValueError):
                    load_config(self.path)

    def test_missing_file(self):
        """Missing configuration yields a user error."""
        with self.assertRaises(ValueError):
            load_config(self.path)

    def test_test_repository(self):
        """Test mode requires an uppercase name and an existing file."""
        self.data.update(test_mode=True, package="A", repository="repo.yaml")
        self.write()
        with self.assertRaises(ValueError):
            load_config(self.path)
        (self.path.parent / "repo.yaml").write_text("A: []\n")
        self.assertTrue(load_config(self.path).test_mode)

    def test_cli_error(self):
        """The CLI returns failure and reports a readable diagnostic."""
        output = StringIO()
        with redirect_stderr(output), redirect_stdout(StringIO()):
            self.assertEqual(main([str(self.path)]), 1)
        self.assertIn("Ошибка:", output.getvalue())

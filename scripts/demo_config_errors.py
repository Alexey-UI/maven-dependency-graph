"""Demonstrate errors for all eight YAML options through the real CLI."""

from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

SUCCESS = 0


def main():
    """Launch one invalid configuration per setting; require failures."""
    root = Path(__file__).resolve().parents[1]
    valid = yaml.safe_load((root / "examples/maven.yaml").read_text())
    invalid = {
        "package": "bad/name", "repository": "ftp://server",
        "test_mode": "yes", "version": "[1,2)",
        "output": "graph.jpg", "ascii_tree": 1,
        "max_depth": -1, "filter_substring": None,
    }
    with tempfile.TemporaryDirectory() as folder:
        for key, value in invalid.items():
            path = Path(folder) / "config.yaml"
            path.write_text(yaml.safe_dump({**valid, key: value}))
            print(f"\nПроверка ошибки: {key}", flush=True)
            result = subprocess.run([sys.executable, "-m",
                                     "dependency_graph", str(path)])
            if result.returncode == SUCCESS:
                raise RuntimeError(f"Не обнаружена ошибка {key}")


if __name__ == "__main__":
    main()

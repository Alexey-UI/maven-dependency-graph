"""Command line entry point; user settings come exclusively from YAML."""

import argparse
import sys

from .config import load_config
from .graph import build_graph
from .test_repository import TestRepository
from .maven import MavenRepository
from .model import Package
from .visualize import ascii_tree, save_visualization


def main(argv=None):
    """Generate Mermaid and PNG and optionally print an ASCII tree."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Maven")
    parser.add_argument("config", help="путь к конфигурации YAML")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        repository_type = (TestRepository if config.test_mode
                           else MavenRepository)
        repository = repository_type(config.repository)
        root = Package(config.package, config.version)
        graph = build_graph(repository, root, config.max_depth,
                            config.filter_substring)
        source = save_visualization(graph, config.output)
        print(f"Mermaid: {source}")
        print(f"PNG: {config.output}")
        if config.ascii_tree:
            print(ascii_tree(graph, root))
    except ValueError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

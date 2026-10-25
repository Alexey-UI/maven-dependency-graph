"""Command line entry point; user settings come exclusively from YAML."""

import argparse
import sys

from .config import load_config
from .maven import MavenRepository
from .model import Package


def main(argv=None):
    """Print direct dependencies for the requested Maven package version."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Maven")
    parser.add_argument("config", help="путь к конфигурации YAML")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if config.test_mode:
            raise ValueError("Тестовый репозиторий появится на этапе 3")
        repository = MavenRepository(config.repository)
        root = Package(config.package, config.version)
        for dependency in repository.dependencies(root):
            print(dependency)
    except ValueError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

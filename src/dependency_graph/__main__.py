"""Command line entry point; user settings come exclusively from YAML."""

import argparse
from dataclasses import asdict
import sys

from .config import load_config


def main(argv=None):
    """Print validated configuration during the prototype stage."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Maven")
    parser.add_argument("config", help="путь к конфигурации YAML")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        for key, value in asdict(config).items():
            print(f"{key}={value}")
    except ValueError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

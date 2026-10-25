"""Validated uppercase-letter repository for reproducible graph exercises."""

import re

from .model import Package
from .yaml_file import load_yaml


class TestRepository:
    """A YAML mapping of package names to ordered dependency lists."""

    def __init__(self, path):
        """Load and validate the complete repository before traversal."""
        self.graph = load_yaml(path)
        if not isinstance(self.graph, dict) or not self.graph:
            raise ValueError("Тестовый репозиторий: нужен непустой словарь")
        for name, children in self.graph.items():
            self.validate_node(name, children)

    def validate_node(self, name, children):
        """Reject invalid names, unknown targets and repeated edges."""
        if not isinstance(name, str) or not re.fullmatch(r"[A-Z]+", name):
            raise ValueError(f"Имя тестового пакета должно быть A..Z: {name}")
        if not isinstance(children, list):
            raise ValueError(f"{name}: зависимости должны быть списком")
        if not all(isinstance(child, str) for child in children):
            raise ValueError(f"{name}: имена зависимостей должны быть строками")
        if len(children) != len(set(children)):
            raise ValueError(f"{name}: повторяющаяся зависимость")
        for child in children:
            if child not in self.graph:
                raise ValueError(f"{name}: неизвестная зависимость {child}")

    def dependencies(self, package):
        """Use the selected configuration version for all test packages."""
        if package.name not in self.graph:
            raise ValueError(f"Пакет не найден: {package.name}")
        return [Package(name, package.version)
                for name in self.graph[package.name]]

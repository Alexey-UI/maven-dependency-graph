"""Small immutable representation of a versioned package."""

from dataclasses import dataclass
import re

from .config import COORDINATE, VERSION


@dataclass(frozen=True)
class Package:
    """Maven coordinates or an uppercase test node with a version."""

    name: str
    version: str

    def __post_init__(self):
        """Prevent invalid coordinates and repository path traversal."""
        if not re.fullmatch(f"(?:{COORDINATE}|[A-Z]+)", self.name):
            raise ValueError(f"Некорректное имя пакета: {self.name}")
        if not re.fullmatch(VERSION, self.version):
            raise ValueError(f"Неподдерживаемая версия: {self.version}")

    def __str__(self):
        """Return readable coordinates for terminal and diagram labels."""
        return f"{self.name}:{self.version}"


@dataclass
class Pom:
    """Effective subset of POM data needed for dependency analysis."""

    properties: dict
    management: dict
    dependencies: list

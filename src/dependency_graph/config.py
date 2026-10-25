"""Load and validate all eight user settings from YAML."""

from dataclasses import dataclass, fields
from pathlib import Path
import re
from urllib.parse import urlsplit

from .yaml_file import load_yaml

MIN_DEPTH = 0
COORDINATE = (r"[A-Za-z0-9_][A-Za-z0-9_.-]*:"
              r"[A-Za-z0-9_][A-Za-z0-9_.-]*")
VERSION = r"[A-Za-z0-9_][A-Za-z0-9_.+-]*"


@dataclass(frozen=True)
class Config:
    """Validated settings; relative paths start at the YAML directory."""

    package: str
    repository: str
    test_mode: bool
    version: str
    output: str
    ascii_tree: bool
    max_depth: int
    filter_substring: str


def validate_types(data):
    """Require exactly the documented keys and exact scalar types."""
    if not isinstance(data, dict):
        raise ValueError("Конфигурация должна быть YAML-словарём")
    expected = {field.name: field.type for field in fields(Config)}
    if data.keys() != expected.keys():
        missing = sorted(expected.keys() - data.keys())
        extra = sorted(data.keys() - expected.keys())
        raise ValueError(f"Пропущены ключи: {missing}; лишние: {extra}")
    for key, kind in expected.items():
        if type(data[key]) is not kind:
            raise ValueError(f"{key}: ожидается {kind.__name__}")
    for key in ("package", "repository", "version", "output"):
        if not data[key].strip():
            raise ValueError(f"{key}: значение не должно быть пустым")


def validate_values(data, base):
    """Validate package, version, depth, repository and output path."""
    pattern = r"[A-Z]+" if data["test_mode"] else COORDINATE
    if not re.fullmatch(pattern, data["package"]):
        raise ValueError("package: ожидается A..Z или groupId:artifactId")
    if not re.fullmatch(VERSION, data["version"]):
        raise ValueError("version: нужна конкретная версия, без диапазонов")
    if data["max_depth"] < MIN_DEPTH:
        raise ValueError("max_depth: ожидается целое число не меньше нуля")
    output = base / data["output"]
    if output.suffix.lower() != ".png" or output.is_dir():
        raise ValueError("output: ожидается имя файла с расширением .png")
    validate_repository(data, base)


def validate_repository(data, base):
    """Check a test file or a plain HTTP(S) repository URL."""
    if data["test_mode"]:
        if not (base / data["repository"]).is_file():
            raise ValueError("repository: файл тестового репозитория не найден")
    else:
        address = urlsplit(data["repository"])
        if address.scheme not in ("http", "https") or not address.hostname:
            raise ValueError("repository: ожидается URL HTTP(S)")
        if address.query or address.fragment or address.username:
            raise ValueError("repository: URL без query, fragment и логина")


def load_config(path):
    """Load settings and normalize filesystem paths."""
    path = Path(path).resolve()
    data = load_yaml(path)
    validate_types(data)
    validate_values(data, path.parent)
    data["output"] = str(path.parent / data["output"])
    if data["test_mode"]:
        data["repository"] = str(path.parent / data["repository"])
    return Config(**data)

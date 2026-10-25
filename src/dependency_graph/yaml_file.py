"""Strict YAML loading shared by configuration and test repositories."""

from pathlib import Path

import yaml


class UniqueLoader(yaml.SafeLoader):
    """Reject ambiguous duplicate mapping keys."""


def unique_mapping(loader, node):
    """Construct a mapping while detecting duplicate keys."""
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise ValueError(f"Повторяющийся ключ YAML: {key}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


def load_yaml(path):
    """Read a UTF-8 YAML file and report actionable errors."""
    try:
        return yaml.load(Path(path).read_text(encoding="utf-8"), UniqueLoader)
    except (OSError, UnicodeError, yaml.YAMLError, TypeError) as error:
        message = f"Не удалось прочитать YAML {path}: {error}"
        raise ValueError(message) from error

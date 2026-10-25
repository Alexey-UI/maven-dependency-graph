"""Parse POM XML and expand Maven property references without Maven APIs."""

import re
from xml.etree import ElementTree

MAX_PROPERTY_PASSES = 50
PROPERTY = re.compile(r"\$\{([^}]+)\}")


def parse_xml(content):
    """Read POM XML with or without Maven's default namespace."""
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as error:
        raise ValueError(f"Некорректный POM XML: {error}") from error
    for element in root.iter():
        element.tag = element.tag.rsplit("}", 1)[-1]
    if root.tag != "project":
        raise ValueError("POM: ожидается корневой элемент project")
    return root


def expand(value, properties):
    """Resolve nested properties, rejecting unknown names and cycles."""
    for _ in range(MAX_PROPERTY_PASSES):
        if not PROPERTY.search(value):
            return value
        updated = PROPERTY.sub(lambda m: properties.get(m[1], m[0]), value)
        if updated == value:
            break
        value = updated
    raise ValueError(f"Не удалось раскрыть свойство POM: {value}")


def text(element, name, default=""):
    """Read one direct child as stripped text."""
    return (element.findtext(name) or default).strip()


def dependency_rows(root, section="dependencies"):
    """Read direct dependency rows, excluding plugin/profile sections."""
    result = []
    for element in root.findall(f"{section}/dependency"):
        row = {item.tag: (item.text or "").strip() for item in element}
        row["exclusions"] = [
            f"{text(item, 'groupId')}:{text(item, 'artifactId')}"
            for item in element.findall("exclusions/exclusion")
        ]
        result.append(row)
    return result


def row_key(row, properties):
    """Identify a dependency by group and artifact."""
    group = expand(row.get("groupId", ""), properties)
    artifact = expand(row.get("artifactId", ""), properties)
    return f"{group}:{artifact}"

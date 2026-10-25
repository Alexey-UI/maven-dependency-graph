"""Fetch and interpret Maven POMs using only the Python standard library."""

from urllib.error import URLError
from urllib.request import Request, urlopen

from .model import Package, Pom
from .pom import dependency_rows, expand, parse_xml, row_key, text

HTTP_TIMEOUT = 30
MAX_POM_BYTES = 5_000_000
RUNTIME_SCOPES = {"compile", "runtime"}


def fetch_pom(url):
    """Download a bounded POM, reporting HTTP and network failures."""
    request = Request(url, headers={"User-Agent": "maven-graph-student/1.0"})
    try:
        with urlopen(request, timeout=HTTP_TIMEOUT) as response:
            content = response.read(MAX_POM_BYTES + 1)
    except (OSError, URLError) as error:
        raise ValueError(f"Не удалось загрузить POM {url}: {error}") from error
    if len(content) > MAX_POM_BYTES:
        raise ValueError(f"POM слишком большой: {url}")
    return content


class MavenRepository:
    """Resolve parent properties, dependency management and imported BOMs."""

    def __init__(self, url, fetch=fetch_pom):
        """Inject transport for deterministic offline tests."""
        self.url = url.rstrip("/")
        self.fetch = fetch
        self.cache = {}
        self.active = set()

    def pom_url(self, package):
        """Construct the standard Maven repository POM path."""
        if ":" not in package.name:
            raise ValueError("Maven требует имя groupId:artifactId")
        group, artifact = package.name.split(":")
        group = group.replace(".", "/")
        version = package.version
        prefix = f"{self.url}/{group}/{artifact}/{version}"
        return f"{prefix}/{artifact}-{version}.pom"

    def effective(self, package):
        """Cache effective models and reject parent/BOM reference cycles."""
        if package in self.cache:
            return self.cache[package]
        if package in self.active:
            raise ValueError(f"Цикл наследования POM/BOM: {package}")
        self.active.add(package)
        try:
            root = parse_xml(self.fetch(self.pom_url(package)))
            model = self.merge_model(package, root)
            self.cache[package] = model
            return model
        finally:
            self.active.remove(package)

    def parent_model(self, root):
        """Load the explicitly declared parent from the same repository."""
        parent = root.find("parent")
        if parent is None:
            return Pom({}, {}, [])
        properties = {item.tag: item.text or ""
                      for item in root.findall("properties/*")}
        name = f"{text(parent, 'groupId')}:{text(parent, 'artifactId')}"
        version = expand(text(parent, "version"), properties)
        return self.effective(Package(name, version))

    def merge_model(self, package, root):
        """Merge inherited properties, managed versions and dependencies."""
        parent = self.parent_model(root)
        group, artifact = package.name.split(":")
        properties = dict(parent.properties)
        properties.update({item.tag: item.text or ""
                           for item in root.findall("properties/*")})
        for prefix in ("project", "pom"):
            properties.update({f"{prefix}.groupId": group,
                               f"{prefix}.artifactId": artifact,
                               f"{prefix}.version": package.version})
        parent_xml = root.find("parent")
        if parent_xml is not None:
            for key in ("groupId", "artifactId", "version"):
                properties[f"project.parent.{key}"] = text(parent_xml, key)
        management = self.managed_rows(root, properties, parent.management)
        dependencies = {row_key(row, properties): row
                        for row in parent.dependencies}
        for row in dependency_rows(root):
            dependencies[row_key(row, properties)] = row
        return Pom(properties, management, list(dependencies.values()))

    def managed_rows(self, root, properties, inherited):
        """Import BOM entries, then apply locally declared management."""
        result = dict(inherited)
        rows = dependency_rows(root, "dependencyManagement/dependencies")
        imported = {}
        for row in rows:
            if row.get("scope") == "import" and row.get("type") == "pom":
                package = Package(row_key(row, properties),
                                  expand(row["version"], properties))
                for key, value in self.effective(package).management.items():
                    imported.setdefault(key, value)
        result.update(imported)
        for row in rows:
            if row.get("scope") != "import":
                resolved = {key: expand(value, properties)
                            for key, value in row.items()
                            if isinstance(value, str)}
                result[row_key(row, properties)] = resolved
        return result

    def dependencies(self, package):
        """Return nonoptional compile/runtime JAR dependencies in POM order."""
        model = self.effective(package)
        result = []
        for row in model.dependencies:
            name = row_key(row, model.properties)
            merged = {**model.management.get(name, {}), **row}
            resolved = {key: expand(value, model.properties)
                        for key, value in merged.items()
                        if isinstance(value, str)}
            if resolved.get("scope", "compile") not in RUNTIME_SCOPES:
                continue
            if resolved.get("optional", "false") == "true":
                continue
            if resolved.get("type", "jar") != "jar":
                raise ValueError(f"Неподдерживаемый тип зависимости: {name}")
            if resolved.get("classifier"):
                raise ValueError(f"Classifier не поддержан: {name}")
            if row.get("exclusions"):
                raise ValueError(f"Exclusions не поддержаны: {name}")
            result.append(Package(name, resolved.get("version", "")))
        return result

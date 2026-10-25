"""Independent verification; Maven is used only here, never by the app."""

from pathlib import Path
import os
import subprocess
import sys
from xml.etree import ElementTree

from dependency_graph.config import load_config
from dependency_graph.graph import build_graph
from dependency_graph.maven import MavenRepository
from dependency_graph.model import Package
from dependency_graph.order import load_order

PLUGIN = "org.apache.maven.plugins:maven-dependency-plugin:3.8.1"
ROOT = Path(__file__).resolve().parents[1]


def make_project(path, package):
    """Create a neutral Maven consumer with one selected dependency."""
    group, artifact = package.name.split(":")
    project = ElementTree.Element("project")
    for key, value in (("modelVersion", "4.0.0"), ("groupId", "demo"),
                       ("artifactId", "comparison"), ("version", "1")):
        ElementTree.SubElement(project, key).text = value
    dependencies = ElementTree.SubElement(project, "dependencies")
    dependency = ElementTree.SubElement(dependencies, "dependency")
    for key, value in (("groupId", group), ("artifactId", artifact),
                       ("version", package.version)):
        ElementTree.SubElement(dependency, key).text = value
    ElementTree.ElementTree(project).write(path, encoding="utf-8")


def maven(work, goal, options):
    """Run a pinned official plugin and preserve its original output."""
    cache = ROOT / "generated/maven-cache"
    command = [os.environ.get("MVN", "mvn"), "-B", "-ntp",
               f"-Dmaven.repo.local={cache}", f"{PLUGIN}:{goal}", *options]
    result = subprocess.run(command, cwd=work, capture_output=True,
                            text=True, timeout=600)
    (work / f"{goal}.log").write_text(result.stdout + result.stderr)
    result.check_returncode()
    return result.stdout


def parse_tgf(path):
    """Normalize Maven TGF coordinates; discard the neutral consumer."""
    nodes_text, edges_text = path.read_text().split("#", 1)
    nodes = {}
    for line in nodes_text.splitlines():
        number, label = line.split(maxsplit=1)
        parts = label.split(":")
        nodes[number] = Package(":".join(parts[:2]), parts[3])
    edges = set()
    for line in edges_text.splitlines():
        if line.strip():
            source, target = line.split()[:2]
            if nodes[source].name != "demo:comparison":
                edges.add((nodes[source], nodes[target]))
    packages = {node for node in nodes.values()
                if node.name != "demo:comparison"}
    return packages, edges


def compare(config_path):
    """Collect actual Maven tree and resolution output for one package."""
    config = load_config(config_path)
    root = Package(config.package, config.version)
    repository = MavenRepository(config.repository)
    graph = build_graph(repository, root, config.max_depth,
                        config.filter_substring)
    work = ROOT / "generated/comparison" / root.name.replace(":", "-")
    work.mkdir(parents=True, exist_ok=True)
    make_project(work / "pom.xml", root)
    maven(work, "tree", ["-Dscope=runtime", "-DoutputType=tgf",
                         "-DoutputFile=tree.tgf"])
    maven(work, "tree", ["-Dscope=runtime", "-DoutputFile=tree.txt"])
    maven(work, "resolve", ["-DincludeScope=runtime", "-Dsort=false",
                            "-DoutputFile=resolved.txt"])
    packages, edges = parse_tgf(work / "tree.tgf")
    own_edges = {(node, child) for node, children in graph.items()
                 for child in children}
    report = [f"Package: {root}",
              f"Nodes match Maven: {set(graph) == packages}",
              f"Edges match Maven: {own_edges == edges}",
              "DFS load order: "
              + " -> ".join(map(str, load_order(graph, root))),
              "Maven dependency:resolve (actual output):",
              (work / "resolved.txt").read_text().strip()]
    (work / "report.txt").write_text("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    for argument in sys.argv[1:]:
        compare(argument)

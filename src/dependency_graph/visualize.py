"""Render the same graph as Mermaid, PNG and an optional ASCII tree."""

from pathlib import Path
import shutil
import subprocess
import tempfile

RENDER_TIMEOUT = 120
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SIGNATURE_BYTES = len(PNG_SIGNATURE)


def mermaid_text(graph):
    """Assign safe diagram IDs while retaining full versioned labels."""
    identifiers = {node: f"n{index}" for index, node in enumerate(graph)}
    lines = ["flowchart TD"]
    for node, identifier in identifiers.items():
        lines.append(f'    {identifier}["{node}"]')
    for node, children in graph.items():
        for child in children:
            lines.append(f"    {identifiers[node]} --> {identifiers[child]}")
    return "\n".join(lines) + "\n"


def ascii_tree(graph, root):
    """Print an iterative tree, distinguishing cycles and shared nodes."""
    lines = [str(root)]
    expanded = {root}
    stack = tree_children(graph, root, "", frozenset({root}))
    while stack:
        node, prefix, last, ancestors = stack.pop()
        branch = "\\-- " if last else "|-- "
        suffix = ""
        if node in ancestors:
            suffix = " [cycle]"
        elif node in expanded:
            suffix = " [shared]"
        lines.append(prefix + branch + str(node) + suffix)
        if suffix:
            continue
        expanded.add(node)
        child_prefix = prefix + ("    " if last else "|   ")
        stack.extend(tree_children(graph, node, child_prefix,
                                   ancestors | {node}))
    return "\n".join(lines)


def tree_children(graph, node, prefix, ancestors):
    """Push children in reverse order for forward terminal presentation."""
    children = graph[node]
    last_index = len(children) - 1
    return [(child, prefix, index == last_index, ancestors)
            for index, child in reversed(list(enumerate(children)))]


def render_png(source, output):
    """Render Mermaid with mmdc and atomically publish a validated PNG."""
    executable = shutil.which("mmdc")
    if executable is None:
        raise ValueError("mmdc не найден: выполните scripts/setup_renderer.sh")
    output = Path(output)
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(dir=output.parent) as folder:
        temporary = Path(folder) / "graph.png"
        command = [executable, "-i", str(source), "-o", str(temporary),
                   "-b", "white", "-s", "2"]
        browser_config = root / ".tools/puppeteer.json"
        if browser_config.exists():
            command.extend(["-p", str(browser_config)])
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=RENDER_TIMEOUT)
        if result.returncode:
            raise ValueError(f"Ошибка Mermaid CLI: {result.stderr.strip()}")
        with temporary.open("rb") as stream:
            if stream.read(SIGNATURE_BYTES) != PNG_SIGNATURE:
                raise ValueError("Mermaid CLI не создал корректный PNG")
        temporary.replace(output)


def save_visualization(graph, output):
    """Write a Mermaid sidecar and render its PNG image."""
    output = Path(output)
    source = output.with_suffix(".mmd")
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(mermaid_text(graph), encoding="utf-8")
        render_png(source, output)
    except (OSError, subprocess.SubprocessError) as error:
        message = f"Не удалось сохранить визуализацию: {error}"
        raise ValueError(message) from error
    return source

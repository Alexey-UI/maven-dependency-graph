"""Dependency traversal with an explicit DFS stack and bounded depth."""


def build_graph(repository, root, max_depth, filter_substring=""):
    """Explore iteratively; re-expand nodes reached by a shorter path."""
    if filter_substring and filter_substring in root.name:
        raise ValueError("Корневой пакет исключён filter_substring")
    graph = {root: []}
    stack = [(root, 0)]
    best_depth = {}
    cache = {}
    while stack:
        node, depth = stack.pop()
        if node in best_depth and best_depth[node] <= depth:
            continue
        best_depth[node] = depth
        if depth >= max_depth:
            continue
        if node not in cache:
            cache[node] = repository.dependencies(node)
        children = filtered_children(cache[node], filter_substring)
        graph[node] = list(dict.fromkeys(children))
        for child in children:
            graph.setdefault(child, [])
        stack.extend((child, depth + 1) for child in reversed(children))
    return graph


def describe_edges(graph):
    """Return a stable human-readable adjacency list for stage three."""
    return "\n".join(
        f"{node} -> {', '.join(map(str, children)) or '(нет зависимостей)'}"
        for node, children in graph.items()
    )


def filtered_children(children, substring):
    """Preserve declaration order while dropping matching package names."""
    if not substring:
        return children
    return [child for child in children if substring not in child.name]

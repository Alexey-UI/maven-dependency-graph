"""Dependency-first load order using iterative DFS postorder."""

VISITING = 1
FINISHED = 2


def load_order(graph, root):
    """Return each package once; reject cycles with a concrete cycle path."""
    order = []
    state = {}
    path = []
    stack = [(root, False)]
    while stack:
        node, leaving = stack.pop()
        if leaving:
            state[node] = FINISHED
            path.pop()
            order.append(node)
            continue
        if state.get(node) == FINISHED:
            continue
        if state.get(node) == VISITING:
            start = path.index(node)
            cycle = " -> ".join(map(str, path[start:] + [node]))
            raise ValueError(f"Цикл: порядок загрузки невозможен: {cycle}")
        state[node] = VISITING
        path.append(node)
        stack.append((node, True))
        stack.extend((child, False) for child in reversed(graph[node]))
    return order

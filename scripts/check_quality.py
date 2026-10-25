"""Check the repository rules listed on pages 5-7 of the assignment."""

import ast
from pathlib import Path
import subprocess
import tokenize

from radon.complexity import cc_visit

MAX_LINES = 1000
MAX_WIDTH = 80
MAX_FUNCTION_LINES = 40
MAX_ARGUMENTS = 7
MAX_COMPLEXITY = 10
NUMERIC_TYPES = (int, float, complex)
FUNCTION_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)
DOCUMENTED_TYPES = (*FUNCTION_TYPES, ast.ClassDef, ast.Module)


def check_node(node, path):
    """Check function size, argument count, docs and numeric comparisons."""
    if isinstance(node, DOCUMENTED_TYPES):
        assert ast.get_docstring(node), f"{path}: отсутствует docstring"
    if isinstance(node, FUNCTION_TYPES):
        size = node.end_lineno - node.lineno + 1
        assert size <= MAX_FUNCTION_LINES, f"{path}: {node.name}: {size} строк"
        args = node.args
        count = len(args.args + args.posonlyargs + args.kwonlyargs)
        count += bool(args.vararg) + bool(args.kwarg)
        assert count <= MAX_ARGUMENTS, f"{path}: {node.name}: аргументы"
    if isinstance(node, ast.Compare):
        for operand in (node.left, *node.comparators):
            if isinstance(operand, ast.Constant):
                assert type(operand.value) not in NUMERIC_TYPES, (
                    f"{path}:{node.lineno}: число в сравнении")


def check_python(path):
    """Inspect source, tests and scripts under the same strict limits."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    assert len(lines) <= MAX_LINES, f"{path}: слишком большой файл"
    for number, line in enumerate(lines, 1):
        assert len(line) <= MAX_WIDTH, f"{path}:{number}: длинная строка"
    for node in ast.walk(ast.parse(source)):
        check_node(node, path)
    check_complexity(source, path)
    with path.open("rb") as stream:
        for token in tokenize.tokenize(stream.readline):
            assert token.type != tokenize.COMMENT, f"{path}: комментарий"


def check_complexity(source, path):
    """Check individual functions and class methods with Radon."""
    for block in cc_visit(source):
        assert block.complexity <= MAX_COMPLEXITY, (
            f"{path}: {block.name}: сложность {block.complexity}")
        for method in getattr(block, "methods", []):
            assert method.complexity <= MAX_COMPLEXITY, (
                f"{path}: {method.name}: сложность {method.complexity}")


def main():
    """Validate project code and print one success line."""
    root = Path(__file__).resolve().parents[1]
    files = [path for folder in ("src", "tests", "scripts")
             for path in (root / folder).rglob("*.py")]
    for path in files:
        check_python(path)
    subprocess.run(["git", "diff", "--check"], cwd=root, check=True)
    print(f"Проверено Python-файлов: {len(files)}; нарушений нет")


if __name__ == "__main__":
    main()

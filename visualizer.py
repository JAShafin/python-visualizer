import argparse
import ast
from pathlib import Path


def visualize_source(source: str) -> str:
    tree = ast.parse(source)
    lines: list[str] = []

    def walk(node: ast.AST, prefix: str = "", is_last: bool = True) -> None:
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{type(node).__name__}")
        children = list(ast.iter_child_nodes(node))
        next_prefix = f"{prefix}{'    ' if is_last else '│   '}"
        for index, child in enumerate(children):
            walk(child, next_prefix, index == len(children) - 1)

    walk(tree)
    return "\n".join(lines)


def visualize_file(path: Path) -> str:
    return visualize_source(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Visualize Python code as an AST tree.")
    parser.add_argument("file", type=Path, help="Path to a Python file")
    args = parser.parse_args()

    try:
        output = visualize_file(args.file)
    except FileNotFoundError:
        parser.error(f"File not found: {args.file}")
    except SyntaxError as exc:
        parser.error(f"Cannot parse Python file: {exc}")
    else:
        print(output)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

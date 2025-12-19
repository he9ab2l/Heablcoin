import ast
import argparse
from pathlib import Path
from typing import Iterable, List, Tuple


SKIP_DUNDER = {"__init__", "__call__", "__enter__", "__exit__", "__repr__", "__iter__", "__next__"}


def iter_py_files(paths: Iterable[str]) -> Iterable[Path]:
    for raw in paths:
        path = Path(raw)
        if path.is_file() and path.suffix == '.py':
            yield path
        elif path.is_dir():
            yield from path.rglob('*.py')


def is_snake_case(name: str) -> bool:
    if name in SKIP_DUNDER:
        return True
    if name.startswith('__') and name.endswith('__'):
        return True
    if not name:
        return True
    return name == name.lower() and '_' in name or name.islower()


def inspect_file(path: Path) -> List[Tuple[int, str, str]]:
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except SyntaxError as exc:
        return [(exc.lineno or 0, '<syntax-error>', exc.msg)]
    violations: List[Tuple[int, str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not is_snake_case(node.name):
                violations.append((node.lineno, 'function', node.name))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description='Check snake_case naming for functions.')
    parser.add_argument('paths', nargs='*', default=['src', 'tools', 'skills', 'utils', 'tests'])
    args = parser.parse_args()
    total = 0
    bad: List[str] = []
    for file_path in iter_py_files(args.paths):
        file_violations = inspect_file(file_path)
        if file_violations:
            total += len(file_violations)
            for lineno, kind, name in file_violations:
                bad.append(f"{file_path}:{lineno} => {kind} '{name}'")
    if bad:
        print('Found naming issues:')
        for line in bad:
            print(f" - {line}")
        print(f"Total issues: {total}")
        return 1
    print('Naming check passed: all function definitions use snake_case.')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())

"""
Batch add concise file headers to Python sources.

Rules:
- Keep UTF-8; do not rewrite files that already have the standard header marker.
- Preserve shebang/encoding lines at the top if present.
- Skip vendor/build caches and hidden folders.
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Set

EXCLUDED_DIRS: Set[str] = {
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "site-packages",
    "node_modules",
    ".tox",
    "dist",
    "build",
    "egg-info",
}

HEADER_MARKER = "# File:"


def header_exists(text: str) -> bool:
    """Detect existing standard header to avoid duplication."""
    return HEADER_MARKER in text.splitlines()[:5]


def format_header(rel_path: str, summary: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d")
    lines = [
        "#" * 60,
        f"# File: {rel_path}",
        f"# Summary: {summary}",
        f"# Generated: {now}",
        "#" * 60,
        "",
    ]
    return "\n".join(lines)


def guess_summary(path: Path) -> str:
    name = path.stem
    if name == "__init__":
        return f"Package initializer for {path.parent.name}"
    return f"Module: {name.replace('_', ' ')}"


def split_preserve_preamble(lines: List[str]) -> tuple[List[str], List[str]]:
    """Keep shebang/encoding lines before inserting header."""
    preserved: List[str] = []
    rest_start = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#!") or ("coding" in stripped and stripped.startswith("#")):
            preserved.append(line)
            rest_start = idx + 1
            continue
        # stop at first non-preamble line
        rest_start = idx
        break
    return preserved, lines[rest_start:]


def process_file(path: Path, base: Path, dry_run: bool = False) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"[WARN] read failed {path}: {exc}")
        return False

    if header_exists(text):
        return True

    rel_path = str(path.relative_to(base)).replace("\\", "/")
    summary = guess_summary(path)
    header = format_header(rel_path, summary)

    lines = text.splitlines()
    preserved, remainder = split_preserve_preamble(lines)
    new_content = "\n".join(preserved + [header] + remainder)

    if dry_run:
        print(f"[DRY] would update {rel_path}")
        print(header)
        return True

    try:
        path.write_text(new_content, encoding="utf-8")
        print(f"[OK] header added: {rel_path}")
        return True
    except Exception as exc:
        print(f"[WARN] write failed {path}: {exc}")
        return False


def iter_python_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        # filter directories in-place
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and not d.startswith(".")]
        for fname in filenames:
            if fname.endswith(".py"):
                yield Path(dirpath) / fname


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch add standard headers to Python files.")
    parser.add_argument("--path", default=".", help="Root directory to scan, default current.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing.")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    success = 0
    failed = 0
    py_files = list(iter_python_files(root))

    print(f"[INFO] scanning {root} ({len(py_files)} python files)")
    for file_path in sorted(py_files):
        if process_file(file_path, root, args.dry_run):
            success += 1
        else:
            failed += 1

    print(f"[SUMMARY] success={success} failed={failed} total={len(py_files)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Cleanup blank lines in Python files.
- Remove blank lines inside function/class bodies
- Keep exactly 2 blank lines between top-level definitions
- Keep 2 blank lines after imports before first def/class
"""
import argparse
import os
from dataclasses import dataclass
from pathlib import Path


SKIP_DIR_NAMES = {
    ".git", ".idea", ".vscode", ".pytest_cache", "__pycache__",
    ".venv", "venv", "env", "node_modules", "dist", "build",
}
SKIP_DIR_PARTS = {os.path.join("data", "mcp_call_backups")}


@dataclass


class FileResult:
    path: Path
    changed: bool
    reason: str = ""


def _should_skip_dir(dir_path: Path) -> bool:
    parts = list(dir_path.parts)
    if any(part in SKIP_DIR_NAMES for part in parts):
        return True
    p = str(dir_path).replace("\\", "/")
    for part in SKIP_DIR_PARTS:
        if p.endswith(part.replace("\\", "/")) or f"/{part.replace('\\', '/')}" in p:
            return True
    return False


def _detect_newline(raw: bytes) -> str:
    return "\r\n" if b"\r\n" in raw else "\n"


def _get_indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _is_def_or_class(line: str) -> bool:
    s = line.strip()
    return (s.startswith("def ") or s.startswith("class ") or
            s.startswith("@") or s.startswith("async def "))


def _normalize_blank_lines(text: str) -> str:
    lines = text.splitlines()
    # Remove leading/trailing blank lines
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()
    if not lines:
        return "\n"
    # First pass: collect non-blank lines with metadata
    items = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.strip() != "":
            items.append(line)
        i += 1
    if not items:
        return "\n"
    # Second pass: insert appropriate blank lines
    out = [items[0]]
    for j in range(1, len(items)):
        curr = items[j]
        prev = items[j - 1]
        curr_indent = _get_indent(curr)
        prev_indent = _get_indent(prev)
        prev_stripped = prev.strip()
        # Before top-level def/class/decorator (indent 0) => 2 blank lines
        if curr_indent == 0 and _is_def_or_class(curr):
            out.append("")
            out.append("")
        # After import block before non-import => 2 blank lines  
        elif (prev_stripped.startswith("import ") or prev_stripped.startswith("from ")):
            curr_stripped = curr.strip()
            if not (curr_stripped.startswith("import ") or curr_stripped.startswith("from ")):
                out.append("")
                out.append("")
        # No blank lines inside function bodies
        out.append(curr)
    return "\n".join(out) + "\n"


def _read_text_utf8(path: Path) -> tuple:
    raw = path.read_bytes()
    newline = _detect_newline(raw)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return None, f"utf-8 decode failed: {e}"
    return text.replace("\r\n", "\n").replace("\r", "\n"), newline


def _write_text_utf8(path: Path, text_unix: str, newline: str) -> None:
    text = text_unix.replace("\n", newline)
    path.write_text(text, encoding="utf-8", newline="")


def process_file(path: Path, apply: bool, backup: bool) -> FileResult:
    loaded = _read_text_utf8(path)
    if loaded[0] is None:
        return FileResult(path=path, changed=False, reason=loaded[1])
    text_unix, newline = loaded
    normalized_unix = _normalize_blank_lines(text_unix)
    original = text_unix if text_unix.endswith("\n") else text_unix + "\n"
    if normalized_unix == original:
        return FileResult(path=path, changed=False)
    if apply:
        if backup:
            bak = path.with_suffix(path.suffix + ".bak")
            if not bak.exists():
                bak.write_bytes(path.read_bytes())
        _write_text_utf8(path, normalized_unix, newline)
    return FileResult(path=path, changed=True)


def iter_py_files(repo_root: Path) -> list:
    results = []
    for root, dirs, files in os.walk(repo_root):
        root_path = Path(root)
        pruned = [d for d in dirs if not _should_skip_dir(root_path / d)]
        dirs[:] = pruned
        for f in files:
            if f.endswith(".py"):
                results.append(root_path / f)
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()
    apply = bool(args.apply)
    if args.dry_run:
        apply = False
    repo_root = Path(args.repo_root).resolve()
    backup = not args.no_backup
    py_files = iter_py_files(repo_root)
    changed = 0
    skipped = 0
    for p in py_files:
        r = process_file(p, apply=apply, backup=backup)
        if r.reason:
            skipped += 1
            print(f"SKIP {p}: {r.reason}")
            continue
        if r.changed:
            changed += 1
            print(f"CHANGED {p}" if apply else f"WOULD_CHANGE {p}")
    print("=" * 60)
    print(f"Scanned: {len(py_files)}")
    print(f"Changed: {changed}{'' if apply else ' (dry-run)'}")
    print(f"Skipped: {skipped}")
    print("Backup: " + ("on" if (apply and backup) else "off"))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())

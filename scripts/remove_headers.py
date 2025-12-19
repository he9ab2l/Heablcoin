#!/usr/bin/env python
"""Remove standardized header blocks from Python files.
This repo previously added a standardized file header block like:
    ############################################################
    # 📘 文件说明：
    # ...
    ############################################################
This script removes that header block while preserving:
- shebang (#!...)
- encoding declaration (PEP-263)
- module docstring and all code
Safety:
- default mode is --dry-run (no writes)
- use --apply to actually write changes
- optional backups via --backup-ext
No third-party dependencies.
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from typing import Iterable, List, Sequence, Set, Tuple


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
    ".mypy_cache",
    ".ruff_cache",
}
HEADER_BORDER = "############################################################"
HEADER_MARKER = "# 📘 文件说明："
_ENCODING_RE = re.compile(r"coding[:=]\s*([-\w.]+)")


def _detect_newline_style(raw: bytes) -> str:
    return "\r\n" if b"\r\n" in raw else "\n"


def _read_text_utf8(path: Path) -> Tuple[str, str, bool]:
    raw = path.read_bytes()
    newline = _detect_newline_style(raw)
    had_trailing_newline = raw.endswith(b"\n")
    for enc in ("utf-8", "utf-8-sig"):
        try:
            return raw.decode(enc), newline, had_trailing_newline
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8", raw, 0, 1, "file is not valid utf-8")


def _write_text_utf8(path: Path, text: str, newline: str, trailing_newline: bool) -> None:
    if trailing_newline and not text.endswith("\n"):
        text += "\n"
    if not trailing_newline:
        text = text.rstrip("\n")
    with path.open("w", encoding="utf-8", newline=newline) as f:
        f.write(text)


def _iter_py_files(root: Path) -> List[Path]:
    out: List[Path] = []
    for p in root.rglob("*.py"):
        if not p.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def _split_preserve_preamble(lines: Sequence[str]) -> Tuple[List[str], int]:
    """Return (preserved_lines, start_index_of_rest)."""
    preserved: List[str] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        if idx == 0 and stripped.startswith("#!"):
            preserved.append(line)
            idx += 1
            continue
        if stripped.startswith("#") and _ENCODING_RE.search(stripped):
            preserved.append(line)
            idx += 1
            continue
        break
    return preserved, idx


def _find_header_block(rest: Sequence[str], max_scan_lines: int = 220) -> Tuple[int, int] | None:
    """If found, return (start_idx, end_idx_exclusive) within rest."""
    if not rest:
        return None
    if rest[0].rstrip("\r\n") != HEADER_BORDER:
        return None
    scan_upto = min(len(rest), max_scan_lines)
    marker_found = False
    end_idx = None
    for i in range(1, scan_upto):
        line = rest[i].rstrip("\r\n")
        if line == HEADER_MARKER:
            marker_found = True
        if i > 1 and line == HEADER_BORDER:
            end_idx = i + 1
            break
    if end_idx is None or not marker_found:
        return None
    return 0, end_idx


def _remove_header_from_text(text: str) -> Tuple[str, bool]:
    lines = text.splitlines(keepends=True)
    preserved, idx = _split_preserve_preamble(lines)
    rest = list(lines[idx:])
    block = _find_header_block(rest)
    if not block:
        return text, False
    start, end = block
    new_rest = rest[:start] + rest[end:]
    # Drop extra leading blank lines introduced by removal.
    while new_rest and new_rest[0].strip() == "":
        new_rest.pop(0)
    new_text = "".join(preserved + new_rest)
    return new_text, new_text != text


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove standardized header comments from .py files.")
    parser.add_argument("--root", default=".", help="Repository root to scan")
    parser.add_argument("--apply", action="store_true", help="Actually write changes")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change (default)")
    parser.add_argument(
        "--backup-ext",
        default=".bak",
        help="Backup extension to use when --apply (set empty to disable backups)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of files to process (0 = no limit)",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    dry_run = args.dry_run or not args.apply
    changed: List[Path] = []
    skipped_non_utf8: List[Tuple[Path, str]] = []
    files = _iter_py_files(root)
    if args.limit and args.limit > 0:
        files = files[: args.limit]
    for path in files:
        try:
            text, newline, trailing_newline = _read_text_utf8(path)
        except UnicodeDecodeError as exc:
            skipped_non_utf8.append((path, str(exc)))
            continue
        new_text, did_change = _remove_header_from_text(text)
        if not did_change:
            continue
        changed.append(path)
        if dry_run:
            continue
        if args.backup_ext:
            backup = path.with_name(path.name + args.backup_ext)
            # If backup already exists, do not overwrite silently.
            if not backup.exists():
                backup.write_bytes(path.read_bytes())
        _write_text_utf8(path, new_text, newline=newline, trailing_newline=trailing_newline)
    if dry_run:
        print(f"[dry-run] would update {len(changed)} files")
    else:
        print(f"updated {len(changed)} files")
    for p in changed[:50]:
        rel = p.relative_to(root).as_posix()
        print(f" - {rel}")
    if len(changed) > 50:
        print(f"... and {len(changed) - 50} more")
    if skipped_non_utf8:
        print(f"skipped {len(skipped_non_utf8)} non-utf8 files")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())

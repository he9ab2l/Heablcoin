#!/usr/bin/env python
"""UTF-8 encoding guard script.

- Enforces UTF-8 (no BOM) for selected text files.
- Keeps existing project rule: forbid ASCII '?' placeholder in 历史记录.json / 任务进度.json.

This script is intentionally dependency-free.
"""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_EXTS = {
    ".md",
    ".mmd",
    ".json",
    ".txt",
    ".py",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".ps1",
    ".sh",
}

DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "site-packages",
    "node_modules",
    "dist",
    "build",
    ".mypy_cache",
    ".ruff_cache",
}


def _iter_files(root: Path, exts: set[str], exclude_dirs: set[str]) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in exclude_dirs for part in p.parts):
            continue
        if p.suffix.lower() not in exts:
            continue
        out.append(p)
    return sorted(out)


def _is_utf8_no_bom(raw: bytes) -> tuple[bool, str]:
    if raw.startswith(b"\xef\xbb\xbf"):
        return False, "has UTF-8 BOM"
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return False, f"not valid utf-8: {exc}"
    return True, "ok"


def _check_no_ascii_question(path: Path) -> tuple[bool, str]:
    # Preserve the repo's anti-corruption rule used by tests.
    raw = path.read_bytes()
    ok, reason = _is_utf8_no_bom(raw)
    if not ok:
        return False, reason
    text = raw.decode("utf-8")
    if "?" in text:
        return False, "contains ASCII '?' placeholder"
    return True, "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check that text files are UTF-8 (no BOM).")
    parser.add_argument("--root", default=".", help="Repo root directory to scan")
    parser.add_argument(
        "--ext",
        action="append",
        default=[],
        help="Extra extension to include (repeatable), e.g. --ext .csv",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Directory name to exclude (repeatable)",
    )
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        help="Path substring to skip (repeatable). Example: --skip '分析/添加功能.md'",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    exts = set(DEFAULT_EXTS)
    exts.update({e if e.startswith(".") else f".{e}" for e in args.ext})

    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS)
    exclude_dirs.update(set(args.exclude_dir))

    skip_substrings = [s.replace("\\", "/") for s in args.skip]

    failures: list[str] = []

    for p in _iter_files(root, exts, exclude_dirs):
        rel = p.relative_to(root).as_posix()
        if any(s in rel for s in skip_substrings):
            continue

        raw = p.read_bytes()
        ok, reason = _is_utf8_no_bom(raw)
        if not ok:
            failures.append(f"{rel}: {reason}")

    # Strong checks for the two project record files.
    for required in ["历史记录.json", "任务进度.json"]:
        path = root / required
        if path.exists():
            ok, reason = _check_no_ascii_question(path)
            if not ok:
                failures.append(f"{required}: {reason}")

    if failures:
        print("UTF-8 check failed:")
        for item in failures:
            print(f" - {item}")
        return 1

    print("UTF-8 check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import os
from dataclasses import dataclass
from pathlib import Path


SKIP_DIR_NAMES = {
    ".git",
    ".idea",
    ".vscode",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
}

SKIP_DIR_PARTS = {
    os.path.join("data", "mcp_call_backups"),
}


@dataclass
class FileResult:
    path: Path
    changed: bool
    reason: str = ""


def _should_skip_dir(dir_path: Path) -> bool:
    parts = list(dir_path.parts)
    if any(part in SKIP_DIR_NAMES for part in parts):
        return True

    # Skip known nested dirs by suffix match on the path string
    p = str(dir_path).replace("\\", "/")
    for part in SKIP_DIR_PARTS:
        if p.endswith(part.replace("\\", "/")) or f"/{part.replace('\\', '/')}" in p:
            return True

    return False


def _detect_newline(raw: bytes) -> str:
    # Prefer CRLF if the file contains it anywhere.
    return "\r\n" if b"\r\n" in raw else "\n"


def _normalize_blank_lines(text: str) -> str:
    lines = text.splitlines()

    # Remove leading blank lines
    while lines and lines[0].strip() == "":
        lines.pop(0)

    # Remove trailing blank lines
    while lines and lines[-1].strip() == "":
        lines.pop()

    out = []
    blank_run = 0
    for line in lines:
        if line.strip() == "":
            blank_run += 1
            # Keep at most 2 consecutive blank lines
            if blank_run <= 2:
                out.append("")
        else:
            blank_run = 0
            out.append(line)

    return "\n".join(out) + "\n"


def _read_text_utf8(path: Path) -> tuple[str, str] | tuple[None, str]:
    raw = path.read_bytes()
    newline = _detect_newline(raw)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return None, f"utf-8 decode failed: {e}"
    return text.replace("\r\n", "\n").replace("\r", "\n"), newline


def _write_text_utf8(path: Path, text_unix: str, newline: str) -> None:
    # Re-apply original newline style
    text = text_unix.replace("\n", newline)
    path.write_text(text, encoding="utf-8", newline="")


def process_file(path: Path, apply: bool, backup: bool) -> FileResult:
    loaded = _read_text_utf8(path)
    if loaded[0] is None:
        return FileResult(path=path, changed=False, reason=loaded[1])

    text_unix, newline = loaded  # type: ignore[assignment]
    normalized_unix = _normalize_blank_lines(text_unix)

    if normalized_unix == (text_unix if text_unix.endswith("\n") else text_unix + "\n"):
        return FileResult(path=path, changed=False)

    if apply:
        if backup:
            bak = path.with_suffix(path.suffix + ".bak")
            if not bak.exists():
                bak.write_bytes(path.read_bytes())
        _write_text_utf8(path, normalized_unix, newline)

    return FileResult(path=path, changed=True)


def iter_py_files(repo_root: Path) -> list[Path]:
    results: list[Path] = []
    for root, dirs, files in os.walk(repo_root):
        root_path = Path(root)

        # Prune dirs
        pruned = []
        for d in dirs:
            if _should_skip_dir(root_path / d):
                continue
            pruned.append(d)
        dirs[:] = pruned

        for f in files:
            if not f.endswith(".py"):
                continue
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

############################################################
# 📘 文件说明：
# 本文件实现的功能：Secret scanner (safe output).
#
# 📋 程序整体伪代码（中文）：
# 1. 初始化主要依赖与变量
# 2. 加载输入数据或接收外部请求
# 3. 执行主要逻辑步骤（如计算、处理、训练、渲染等）
# 4. 输出或返回结果
# 5. 异常处理与资源释放
#
# 🔄 程序流程图（逻辑流）：
# ┌──────────┐
# │  输入数据 │
# └─────┬────┘
#       ↓
# ┌────────────┐
# │  核心处理逻辑 │
# └─────┬──────┘
#       ↓
# ┌──────────┐
# │  输出结果 │
# └──────────┘
#
# 📊 数据管道说明：
# 数据流向：输入源 → 数据清洗/转换 → 核心算法模块 → 输出目标（文件 / 接口 / 终端）
#
# 🧩 文件结构：
# - 依赖（标准库）：__future__, argparse, dataclasses, os, re, subprocess, sys, typing
# - 依赖（第三方）：无
# - 依赖（本地）：无
#
# 🕒 创建时间：2025-12-19
############################################################

"""
Secret scanner (safe output).

Design goals:
- Scan only staged files by default.
- Detect common secret token patterns.
- Never print secret content; only file paths + hit counts.

Usage:
  python scripts/scan_secrets.py --staged
  python scripts/scan_secrets.py --files path1 path2
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class Pattern:
    name: str
    regex: re.Pattern[str]


PATTERNS: List[Pattern] = [
    Pattern("openai_style_sk", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    Pattern("google_ai_key", re.compile(r"AIza[0-9A-Za-z\\-_]{20,}")),
    Pattern("serverchan_sendkey", re.compile(r"SCT[0-9A-Za-z]{20,}")),
    Pattern("slack_token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}")),
    Pattern("github_token", re.compile(r"(?:ghp_[0-9A-Za-z]{20,}|github_pat_[0-9A-Za-z_]{20,})")),
    Pattern("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]


def _run_git(args: Sequence[str]) -> str:
    try:
        out = subprocess.check_output(["git", *args], stderr=subprocess.STDOUT)
    except FileNotFoundError:
        raise SystemExit("git not found in PATH")
    except subprocess.CalledProcessError as e:
        msg = e.output.decode("utf-8", errors="replace").strip()
        raise SystemExit(f"git failed: {' '.join(args)}\n{msg}")
    return out.decode("utf-8", errors="replace")


def _staged_files() -> List[str]:
    out = _run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMRT"])
    files = [line.strip() for line in out.splitlines() if line.strip()]
    return files


def _repo_root() -> str:
    return _run_git(["rev-parse", "--show-toplevel"]).strip()


def _read_text(repo_root: str, path: str) -> str:
    full_path = path if os.path.isabs(path) else os.path.join(repo_root, path)
    try:
        with open(full_path, "rb") as f:
            raw = f.read()
    except OSError:
        return ""
    # Use UTF-8 with replacement; secret patterns are ASCII-like.
    return raw.decode("utf-8", errors="replace")


def _scan_files(files: Iterable[str]) -> List[str]:
    violations: List[str] = []
    repo_root = _repo_root()

    for path in files:
        norm = path.replace("\\", "/")

        # Quick filename guards: never commit real env files or private keys.
        base = os.path.basename(norm).lower()
        if base in {".env", ".env.local", ".env.production", ".env.prod"}:
            violations.append(f"forbidden_file file={norm} reason=env_file")
            continue
        if base in {"id_rsa", "id_ed25519"} or base.endswith((".pem", ".key", ".p12")):
            violations.append(f"forbidden_file file={norm} reason=key_material")
            continue

        text = _read_text(repo_root, path)
        if not text:
            continue

        for pattern in PATTERNS:
            hits = len(pattern.regex.findall(text))
            if hits:
                violations.append(f"pattern_hit pattern={pattern.name} file={norm} hits={hits}")

    return violations


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Scan files for common secret patterns (safe output).")
    parser.add_argument("--staged", action="store_true", help="Scan staged files (default).")
    parser.add_argument("--files", nargs="*", default=[], help="Explicit file list to scan.")
    args = parser.parse_args(list(argv))

    files: List[str] = list(args.files) if args.files else _staged_files()

    if not files:
        print("OK: no files to scan")
        return 0

    violations = _scan_files(files)
    if not violations:
        print("OK: no secret patterns found")
        return 0

    print("FAIL: potential secrets detected")
    for row in violations:
        print(row)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

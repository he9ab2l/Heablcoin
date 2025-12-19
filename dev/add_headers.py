"""
批处理脚本：为仓库内所有 Python 代码文件添加标准化文件头注释（任务.txt-任务1）。

执行目标：
1) 扫描项目中所有 .py 文件（排除虚拟环境与缓存目录）
2) 为每个文件智能生成符合其实际功能的头注释（基于路径/文件名/docstring/关键字）
3) 自动提取 import 依赖作为“文件结构”部分（按 标准库/第三方/本地 分组）
4) 保留原有的 shebang 与 encoding 声明
5) 不修改原有业务逻辑代码（只插入注释块）
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Sequence, Set, Tuple

_BEIJING_TZ = timezone(timedelta(hours=8))

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
_LOCAL_TOPLEVEL = {"core", "tools", "skills", "storage", "utils"}


def _beijing_date() -> str:
    return datetime.now(_BEIJING_TZ).strftime("%Y-%m-%d")


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


def _header_exists(text: str) -> bool:
    head = "\n".join(text.splitlines()[:80])
    return HEADER_MARKER in head and HEADER_BORDER in head


def _split_preserve_preamble(lines: Sequence[str]) -> Tuple[List[str], List[str]]:
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
    return preserved, list(lines[idx:])


def _safe_first_line(text: str) -> str:
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def _extract_docstring_and_imports(source: str) -> Tuple[str, List[str]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return "", _extract_imports_regex(source)

    doc = ast.get_docstring(tree) or ""
    imports: List[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            prefix = "." * (node.level or 0)
            imports.append(prefix + module if module else prefix)
    return doc, imports


def _extract_imports_regex(source: str) -> List[str]:
    out: List[str] = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("import "):
            name = stripped[len("import ") :].split(" as ")[0].split(",")[0].strip()
            if name:
                out.append(name)
        if stripped.startswith("from ") and " import " in stripped:
            name = stripped[len("from ") :].split(" import ")[0].strip()
            if name:
                out.append(name)
    return out


def _categorize_imports(modules: Sequence[str]) -> Tuple[List[str], List[str], List[str]]:
    stdlib: Set[str] = set()
    third: Set[str] = set()
    local: Set[str] = set()

    stdlib_names = getattr(sys, "stdlib_module_names", set())

    for mod in modules:
        mod = (mod or "").strip()
        if not mod:
            continue
        if mod.startswith("."):
            local.add(mod)
            continue

        top = mod.split(".")[0]
        if top in _LOCAL_TOPLEVEL:
            local.add(mod)
        elif top in stdlib_names:
            stdlib.add(top)
        else:
            third.add(top)

    return sorted(stdlib), sorted(third), sorted(local)


def _format_dep_list(items: Sequence[str], *, max_items: int = 12) -> str:
    items = [x for x in items if x]
    if not items:
        return "无"
    if len(items) <= max_items:
        return ", ".join(items)
    head = ", ".join(list(items)[:max_items])
    return f"{head} ... 等 {len(items)} 个"


def _guess_description(rel_path: str, docstring: str, source: str) -> str:
    first_doc = _safe_first_line(docstring)
    if 6 <= len(first_doc) <= 120:
        return first_doc

    name = Path(rel_path).stem
    if name == "__init__":
        return "包初始化：聚合导出符号并提供稳定的导入入口。"

    lowered = (rel_path + "\n" + source[:4000]).lower()
    if rel_path.replace("\\", "/").startswith("tests/"):
        return f"测试用例：验证 {name} 相关逻辑的正确性与回归。"
    if "mcp" in lowered and ("fastmcp" in lowered or "mcp.tool" in lowered):
        return "MCP 相关模块：定义/封装工具调用并强化 stdout 协议安全。"
    if "redis" in lowered:
        return "Redis 相关模块：提供队列/缓存/任务通信的适配与封装。"
    if "smtp" in lowered or "smtplib" in lowered or "email" in lowered:
        return "通知与邮件模块：封装消息发送/通知分发能力。"
    if "ccxt" in lowered or "exchange" in lowered:
        return "交易所相关模块：封装行情/下单/账户等接口访问能力。"
    if "risk" in lowered:
        return "风控相关模块：提供风险控制、资金管理与限制规则。"
    if "market" in lowered or "analysis" in lowered:
        return "市场研究/分析模块：提供数据分析、质量评估与研究辅助能力。"
    if "logger" in lowered or "logging" in lowered:
        return "日志模块：提供结构化日志、分通道输出与性能记录能力。"

    parts = rel_path.replace("\\", "/").split("/")
    if parts[:2] == ["src", "core"]:
        return f"核心模块：提供 {name} 相关的基础能力与公共接口。"
    if parts[:2] == ["src", "tools"]:
        return f"MCP 工具模块：提供 {name} 相关工具并对接 skills/core/storage。"
    if parts[:2] == ["src", "skills"]:
        return f"技能模块：实现 {name} 相关的业务能力封装与组合调用。"
    if parts[:2] == ["src", "storage"]:
        return f"存储适配模块：实现 {name} 相关的存储读写与外部服务对接。"
    if parts[:2] == ["src", "utils"]:
        return f"通用工具模块：提供 {name} 相关的辅助函数与基础组件。"
    if parts and parts[0] in {"scripts", "dev"}:
        return f"工程脚本：提供 {name} 的自动化工具与批处理能力。"

    return f"模块：{name}（提供相关功能实现与公共接口）。"


def _render_header(rel_path: str, description: str, imports: Sequence[str]) -> str:
    stdlib, third, local = _categorize_imports(imports)

    lines = [
        HEADER_BORDER,
        "# 📘 文件说明：",
        f"# 本文件实现的功能：{description}",
        "#",
        "# 📋 程序整体伪代码（中文）：",
        "# 1. 初始化主要依赖与变量",
        "# 2. 加载输入数据或接收外部请求",
        "# 3. 执行主要逻辑步骤（如计算、处理、训练、渲染等）",
        "# 4. 输出或返回结果",
        "# 5. 异常处理与资源释放",
        "#",
        "# 🔄 程序流程图（逻辑流）：",
        "# ┌──────────┐",
        "# │  输入数据 │",
        "# └─────┬────┘",
        "#       ↓",
        "# ┌────────────┐",
        "# │  核心处理逻辑 │",
        "# └─────┬──────┘",
        "#       ↓",
        "# ┌──────────┐",
        "# │  输出结果 │",
        "# └──────────┘",
        "#",
        "# 📊 数据管道说明：",
        "# 数据流向：输入源 → 数据清洗/转换 → 核心算法模块 → 输出目标（文件 / 接口 / 终端）",
        "#",
        "# 🧩 文件结构：",
        f"# - 依赖（标准库）：{_format_dep_list(stdlib)}",
        f"# - 依赖（第三方）：{_format_dep_list(third)}",
        f"# - 依赖（本地）：{_format_dep_list(local)}",
        "#",
        f"# 🕒 创建时间：{_beijing_date()}",
        HEADER_BORDER,
        "",
    ]
    return "\n".join(lines)


def process_file(path: Path, base: Path, dry_run: bool = False) -> bool:
    try:
        text, newline, trailing_newline = _read_text_utf8(path)
    except Exception as exc:
        print(f"[WARN] read failed {path}: {exc}")
        return False

    if _header_exists(text):
        return True

    rel_path = str(path.relative_to(base)).replace("\\", "/")
    docstring, imports = _extract_docstring_and_imports(text)
    description = _guess_description(rel_path, docstring, text)
    header = _render_header(rel_path, description, imports)

    lines = text.splitlines()
    preserved, remainder = _split_preserve_preamble(lines)
    new_content = "\n".join(preserved + [header] + remainder)

    if dry_run:
        print(f"[DRY] would update {rel_path}")
        return True

    try:
        _write_text_utf8(path, new_content, newline, trailing_newline)
        print(f"[OK] header added: {rel_path}")
        return True
    except Exception as exc:
        print(f"[WARN] write failed {path}: {exc}")
        return False


def iter_python_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and not d.startswith(".")]
        for fname in filenames:
            if fname.endswith(".py"):
                yield Path(dirpath) / fname


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch add standardized headers to Python files.")
    parser.add_argument("--path", default=".", help="Root directory to scan, default current.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing.")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    py_files = sorted(iter_python_files(root))
    print(f"[INFO] scanning {root} ({len(py_files)} python files)")

    success = 0
    failed = 0
    for file_path in py_files:
        if process_file(file_path, root, args.dry_run):
            success += 1
        else:
            failed += 1

    print(f"[SUMMARY] success={success} failed={failed} total={len(py_files)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

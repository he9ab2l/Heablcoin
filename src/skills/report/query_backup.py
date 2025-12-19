############################################################
# 📘 文件说明：
# 本文件实现的功能：技能模块：实现 query_backup 相关的业务能力封装与组合调用。
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
# - 依赖（标准库）：__future__, datetime, json, pathlib, re, typing
# - 依赖（第三方）：无
# - 依赖（本地）：utils.project_paths
#
# 🕒 创建时间：2025-12-19
############################################################

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from utils.project_paths import PROJECT_ROOT


def _safe_filename_component(value: str) -> str:
    v = str(value or "").strip()
    v = v.replace("/", "_").replace("\\", "_")
    v = re.sub(r"[^A-Za-z0-9._-]+", "_", v)
    v = re.sub(r"_+", "_", v).strip("_")
    return v or "unknown"


def query_backups_base_dir() -> Path:
    return PROJECT_ROOT / "reports" / "query_backups"


def save_query_backup(
    tool_name: str,
    title: str,
    content: str,
    params: Dict[str, Any],
    return_format: str = "markdown",
    extra_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    created_at = datetime.now()
    date_str = created_at.strftime("%Y%m%d")
    ts_str = created_at.strftime("%Y%m%d_%H%M%S")

    safe_tool = _safe_filename_component(tool_name)
    safe_title = _safe_filename_component(title)

    out_dir = query_backups_base_dir() / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    fmt = (return_format or "markdown").lower().strip()
    ext = "md" if fmt == "markdown" else "json" if fmt == "json" else "txt"

    base = f"{ts_str}__{safe_tool}__{safe_title}"
    out_path = out_dir / f"{base}.{ext}"
    meta_path = out_dir / f"{base}.meta.json"

    out_path.write_text(str(content or ""), encoding="utf-8", newline="\n")

    meta: Dict[str, Any] = {
        "tool": tool_name,
        "title": title,
        "created_at": created_at.isoformat(),
        "return_format": fmt,
        "params": params,
        "paths": {"content": str(out_path), "meta": str(meta_path)},
    }
    if extra_meta:
        meta.update(extra_meta)

    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return {"content": str(out_path), "meta": str(meta_path)}


__all__ = ["query_backups_base_dir", "save_query_backup"]

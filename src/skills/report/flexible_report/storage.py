############################################################
# 📘 文件说明：
# 本文件实现的功能：通知与邮件模块：封装消息发送/通知分发能力。
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
# - 依赖（标准库）：__future__, datetime, json, pathlib, typing
# - 依赖（第三方）：无
# - 依赖（本地）：.utils, utils.project_paths
#
# 🕒 创建时间：2025-12-19
############################################################

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, Optional

from .utils import safe_filename_component
from utils.project_paths import PROJECT_ROOT


def reports_base_dir() -> Path:
    return PROJECT_ROOT / "reports" / "flexible_report"


def save_backup(
    title: str,
    full_html: str,
    enabled_modules: Dict[str, bool],
    send_result: Dict[str, Any],
    resolved_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    created_at = datetime.now()
    date_str = created_at.strftime("%Y%m%d")
    ts_str = created_at.strftime("%Y%m%d_%H%M%S")
    safe_title = safe_filename_component(title)
    out_dir = reports_base_dir() / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    base = f"{ts_str}__{safe_title}"
    html_path = out_dir / f"{base}.html"
    meta_path = out_dir / f"{base}.meta.json"
    data_path = out_dir / f"{base}.data.json"

    html_path.write_text(str(full_html or ""), encoding="utf-8", newline="\n")
    if resolved_data is None:
        resolved_data = {}
    data_path.write_text(json.dumps(resolved_data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    meta = {
        "title": title,
        "created_at": created_at.isoformat(),
        "modules": {k: bool(v) for k, v in enabled_modules.items()},
        "paths": {"html": str(html_path), "meta": str(meta_path), "data": str(data_path)},
        "email": {"result": send_result},
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return {"html": str(html_path), "meta": str(meta_path), "data": str(data_path)}


__all__ = ["reports_base_dir", "save_backup"]

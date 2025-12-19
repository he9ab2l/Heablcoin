############################################################
# 📘 文件说明：
# 本文件实现的功能：技能模块：实现 storage 相关的业务能力封装与组合调用。
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
# - 依赖（标准库）：__future__, datetime, json, pathlib, typing, uuid
# - 依赖（第三方）：无
# - 依赖（本地）：utils.project_paths
#
# 🕒 创建时间：2025-12-19
############################################################

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.project_paths import PROJECT_ROOT


def learning_store_dir() -> Path:
    out = PROJECT_ROOT / "reports" / "learning_sessions"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _session_path(session_id: str) -> Path:
    return learning_store_dir() / f"{session_id}.json"


def create_session(kind: str, prompt: str, payload: Dict[str, Any], answer_key: Dict[str, Any]) -> str:
    session_id = uuid.uuid4().hex
    created_at = datetime.now().isoformat()
    data = {
        "id": session_id,
        "kind": str(kind or "").strip() or "unknown",
        "created_at": created_at,
        "prompt": str(prompt or ""),
        "payload": payload or {},
        "answer_key": answer_key or {},
        "submissions": [],
    }
    _session_path(session_id).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return session_id


def load_session(session_id: str) -> Optional[Dict[str, Any]]:
    p = _session_path(session_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_session(session: Dict[str, Any]) -> bool:
    sid = str(session.get("id") or "").strip()
    if not sid:
        return False
    p = _session_path(sid)
    try:
        p.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        return True
    except Exception:
        return False


def append_submission(session_id: str, answer: str, result: Dict[str, Any]) -> bool:
    session = load_session(session_id)
    if not isinstance(session, dict):
        return False
    subs: List[Dict[str, Any]] = session.get("submissions") if isinstance(session.get("submissions"), list) else []
    subs.append({
        "at": datetime.now().isoformat(),
        "answer": str(answer or ""),
        "result": result or {},
    })
    session["submissions"] = subs
    return save_session(session)


def list_sessions(limit: int = 20) -> List[Dict[str, Any]]:
    lim = int(limit) if limit and int(limit) > 0 else 20
    base = learning_store_dir()
    items = sorted(base.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: List[Dict[str, Any]] = []
    for p in items[:lim]:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        out.append({
            "id": data.get("id"),
            "kind": data.get("kind"),
            "created_at": data.get("created_at"),
            "prompt": (data.get("prompt") or "")[:120],
            "submissions": len(data.get("submissions") or []),
        })
    return out


__all__ = [
    "learning_store_dir",
    "create_session",
    "load_session",
    "save_session",
    "append_submission",
    "list_sessions",
]

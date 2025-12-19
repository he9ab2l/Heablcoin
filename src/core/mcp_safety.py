############################################################
# 📘 文件说明：
# 本文件实现的功能：MCP Tool 安全封装（异常隔离 + 软禁用）
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
# - 依赖（标准库）：__future__, contextlib, datetime, functools, json, logging, pathlib, sys, time, traceback, typing
# - 依赖（第三方）：无
# - 依赖（本地）：core.tool_registry, utils.env_helpers
#
# 🕒 创建时间：2025-12-19
############################################################

"""
MCP Tool 安全封装（异常隔离 + 软禁用）

注意：MCP 通过 stdout 传输 JSON-RPC；任何非协议输出都会污染通道。
本模块仅返回字符串/JSON，不做 print。
"""

from __future__ import annotations

import contextlib
import functools
import json
import logging
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from core.tool_registry import is_tool_enabled, register_tool
from utils.env_helpers import env_bool, env_int, env_str, resolve_path


_SENSITIVE_KEYWORDS = (
    "key",
    "secret",
    "password",
    "pass",
    "token",
    "api_key",
    "apikey",
    "authorization",
)


def _beijing_now() -> datetime:
    return datetime.now(timezone(timedelta(hours=8)))


def _safe_filename_component(value: str) -> str:
    value = (value or "").strip().replace("\\", "_").replace("/", "_")
    keep = []
    for ch in value:
        if ch.isalnum() or ch in "._-":
            keep.append(ch)
        else:
            keep.append("_")
    out = "".join(keep)
    while "__" in out:
        out = out.replace("__", "_")
    out = out.strip("_")
    return out or "unknown"


def _looks_sensitive_key(key: str) -> bool:
    k = (key or "").strip().lower()
    return any(s in k for s in _SENSITIVE_KEYWORDS)


def _truncate_text(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if text is None:
        return ""
    text = str(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"...(truncated,len={len(text)})"


def _sanitize(obj: Any, *, max_str_chars: int = 2000, _depth: int = 0) -> Any:
    if _depth > 6:
        return "<depth_limit>"

    if obj is None:
        return None
    if isinstance(obj, (bool, int, float)):
        return obj
    if isinstance(obj, str):
        return _truncate_text(obj, max_str_chars)
    if isinstance(obj, (list, tuple)):
        return [_sanitize(x, max_str_chars=max_str_chars, _depth=_depth + 1) for x in obj]
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            key = str(k)
            if _looks_sensitive_key(key):
                out[key] = "<redacted>"
            else:
                out[key] = _sanitize(v, max_str_chars=max_str_chars, _depth=_depth + 1)
        return out

    # Fallback: keep it stable and non-crashing
    return _truncate_text(repr(obj), max_str_chars)


def _get_mcp_logger() -> logging.Logger:
    """
    Prefer SmartLogger('mcp') when enabled; otherwise fall back to std logging.
    Must never raise.
    """
    try:
        if env_bool("ENABLE_SMART_LOGGER", True):
            from utils.smart_logger import get_logger as _get_logger

            return _get_logger("mcp")
    except Exception:
        pass
    return logging.getLogger("heablcoin.mcp")


def _write_call_backup(payload: dict[str, Any]) -> None:
    if not env_bool("MCP_CALL_BACKUP_ENABLED", True):
        return

    base = env_str("MCP_CALL_BACKUP_DIR", "data/mcp_call_backups")
    base_path = Path(resolve_path(base, "data/mcp_call_backups"))
    day = _beijing_now().strftime("%Y%m%d")
    out_dir = base_path / day
    out_dir.mkdir(parents=True, exist_ok=True)

    tool = _safe_filename_component(str(payload.get("tool") or "tool"))
    call_id = _safe_filename_component(str(payload.get("call_id") or "call"))
    ts = _beijing_now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{ts}__{tool}__{call_id}.json"

    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def mcp_tool_safe(func: Callable) -> Callable:
    """
    MCP 工具安全装饰器
    - 捕获所有异常，防止 MCP Server 崩溃
    - 工具可被运行时禁用（软禁用）：返回说明文本，不执行真实逻辑
    - 记录完整堆栈到日志供调试
    - 保持 MCP 连接不断开
    """
    tool_name = getattr(func, "__name__", "unknown")
    register_tool(
        name=tool_name,
        description=(getattr(func, "__doc__", "") or "").strip(),
        module=getattr(func, "__module__", "") or "",
    )

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        call_id = f"{int(time.time() * 1000)}"
        start = time.time()
        log_enabled = env_bool("MCP_CALL_LOG_ENABLED", True)
        include_args = env_bool("MCP_CALL_LOG_INCLUDE_ARGS", True)
        max_value_chars = env_int("MCP_CALL_LOG_MAX_VALUE_CHARS", 2000)
        max_result_chars = env_int("MCP_CALL_LOG_MAX_RESULT_CHARS", 2000)

        logger = _get_mcp_logger() if log_enabled else None

        if not is_tool_enabled(tool_name):
            if logger:
                try:
                    logger.info(
                        "tool_disabled",
                        extra={
                            "context": {
                                "call_id": call_id,
                                "tool": tool_name,
                                "status": "disabled",
                            }
                        },
                    )
                except Exception:
                    pass
            return (
                "工具已禁用。\n\n"
                f"- tool: `{tool_name}`\n"
                "- 操作: 使用 `set_tool_enabled(tool_name, true)` 重新启用\n"
            )

        try:
            if logger:
                try:
                    ctx: dict[str, Any] = {"call_id": call_id, "tool": tool_name, "status": "start"}
                    if include_args:
                        ctx["args"] = _sanitize(list(args), max_str_chars=max_value_chars)
                        ctx["kwargs"] = _sanitize(dict(kwargs), max_str_chars=max_value_chars)
                    logger.info("tool_call", extra={"context": ctx})
                except Exception:
                    pass

            with contextlib.redirect_stdout(sys.stderr):
                result = func(*args, **kwargs)

            duration_ms = int((time.time() - start) * 1000)

            if logger:
                try:
                    ctx = {
                        "call_id": call_id,
                        "tool": tool_name,
                        "status": "success",
                        "duration_ms": duration_ms,
                        "result_type": type(result).__name__,
                        "result_preview": _sanitize(result, max_str_chars=max_result_chars),
                    }
                    logger.info("tool_result", extra={"context": ctx})
                except Exception:
                    pass

            try:
                payload = {
                    "timestamp": _beijing_now().strftime("%Y-%m-%d %H:%M:%S"),
                    "call_id": call_id,
                    "tool": tool_name,
                    "module": getattr(func, "__module__", "") or "",
                    "status": "success",
                    "duration_ms": duration_ms,
                }
                if include_args:
                    payload["args"] = _sanitize(list(args), max_str_chars=max_value_chars)
                    payload["kwargs"] = _sanitize(dict(kwargs), max_str_chars=max_value_chars)
                payload["result_type"] = type(result).__name__
                payload["result"] = _sanitize(result, max_str_chars=env_int("MCP_CALL_BACKUP_MAX_RESULT_CHARS", 20000))
                _write_call_backup(payload)
            except Exception:
                pass

            return result
        except Exception as e:
            error_detail = {
                "tool": tool_name,
                "error_type": type(e).__name__,
                "error_msg": str(e),
                "traceback": traceback.format_exc(),
            }

            logging.error("[MCP Tool Error] %s", error_detail)
            duration_ms = int((time.time() - start) * 1000)

            if logger:
                try:
                    logger.error(
                        "tool_error",
                        extra={
                            "context": {
                                "call_id": call_id,
                                "tool": tool_name,
                                "status": "error",
                                "duration_ms": duration_ms,
                                "error_type": type(e).__name__,
                                "error_msg": str(e),
                            }
                        },
                    )
                except Exception:
                    pass

            try:
                payload = {
                    "timestamp": _beijing_now().strftime("%Y-%m-%d %H:%M:%S"),
                    "call_id": call_id,
                    "tool": tool_name,
                    "module": getattr(func, "__module__", "") or "",
                    "status": "error",
                    "duration_ms": duration_ms,
                    "error_type": type(e).__name__,
                    "error_msg": str(e),
                    "traceback": error_detail["traceback"] if env_bool("MCP_CALL_BACKUP_INCLUDE_TRACEBACK", False) else "",
                }
                if include_args:
                    payload["args"] = _sanitize(list(args), max_str_chars=max_value_chars)
                    payload["kwargs"] = _sanitize(dict(kwargs), max_str_chars=max_value_chars)
                _write_call_backup(payload)
            except Exception:
                pass

            msg = (
                "工具执行失败。\n\n"
                f"错误类型: {type(e).__name__}\n"
                f"错误信息: {str(e)}\n\n"
                "建议:\n"
                "- 检查参数是否正确\n"
                "- 查看日志文件获取详细信息\n"
                "- 稍后重试\n\n"
                f"tool: `{tool_name}`"
            )

            if env_bool("DEBUG_MODE", False):
                msg += f"\n\n调试信息:\n```\n{error_detail['traceback']}\n```"

            return msg

    return wrapper


__all__ = ["mcp_tool_safe"]

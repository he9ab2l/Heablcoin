"""
MCP Tool 安全封装（异常隔离 + 软禁用）

注意：MCP 通过 stdout 传输 JSON-RPC；任何非协议输出都会污染通道。
本模块仅返回字符串/JSON，不做 print。
"""

from __future__ import annotations

import functools
import logging
import traceback
from typing import Any, Callable

from core.tool_registry import is_tool_enabled, register_tool
from utils.env_helpers import env_bool


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
        if not is_tool_enabled(tool_name):
            return (
                "工具已禁用。\n\n"
                f"- tool: `{tool_name}`\n"
                "- 操作: 使用 `set_tool_enabled(tool_name, true)` 重新启用\n"
            )

        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_detail = {
                "tool": tool_name,
                "error_type": type(e).__name__,
                "error_msg": str(e),
                "traceback": traceback.format_exc(),
            }

            logging.error("[MCP Tool Error] %s", error_detail)

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


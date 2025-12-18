"""管理类 MCP Tools：工具注册表/开关/状态查询。"""

from __future__ import annotations

import json
from typing import Any

from core.mcp_safety import mcp_tool_safe
from core.tool_registry import (
    list_tools as _list_tools,
    reset_tool_overrides as _reset_tool_overrides,
    set_tool_enabled as _set_tool_enabled,
)


def register_tools(mcp: Any) -> None:
    @mcp.tool()
    @mcp_tool_safe
    def list_tools() -> str:
        """列出所有已注册的 MCP 工具及其启用状态（JSON）。"""
        return json.dumps({"tools": _list_tools()}, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def set_tool_enabled(tool_name: str, enabled: bool) -> str:
        """运行时启用/禁用指定 MCP 工具（软禁用）。"""
        _set_tool_enabled(tool_name, enabled)
        return json.dumps({"tool": tool_name, "enabled": bool(enabled)}, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def reset_tool_overrides() -> str:
        """清空所有运行时工具开关覆盖。"""
        _reset_tool_overrides()
        return json.dumps({"success": True}, ensure_ascii=False, indent=2)


__all__ = ["register_tools"]

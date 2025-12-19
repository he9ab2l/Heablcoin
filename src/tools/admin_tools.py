############################################################
# 📘 文件说明：
# 本文件实现的功能：管理类 MCP Tools：工具注册表/开关/状态查询。
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
# - 依赖（标准库）：__future__, json, typing
# - 依赖（第三方）：无
# - 依赖（本地）：core.mcp_safety, core.tool_registry
#
# 🕒 创建时间：2025-12-19
############################################################

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

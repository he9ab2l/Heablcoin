############################################################
# 📘 文件说明：
# 本文件实现的功能：MCP Tool 注册表（可开关/可观测）
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
# - 依赖（标准库）：__future__, dataclasses, os, time, typing
# - 依赖（第三方）：无
# - 依赖（本地）：无
#
# 🕒 创建时间：2025-12-19
############################################################

"""
MCP Tool 注册表（可开关/可观测）

目标：
- 记录所有已注册的 MCP tool 元信息（描述、模块、默认开关、标签）
- 支持运行时 enable/disable（无法动态卸载 FastMCP tool 时，采用“软禁用”策略）
- 支持环境变量开关（启动时/运行时均可生效）

环境变量：
- TOOLS_DISABLED: 逗号分隔的 tool 名称列表（默认全部启用）
- TOOLS_ENABLED_ONLY: 逗号分隔白名单（非空时仅白名单启用）
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


def _parse_csv(value: str) -> List[str]:
    parts = [p.strip() for p in (value or "").split(",")]
    return [p for p in parts if p]


@dataclass
class ToolMeta:
    name: str
    description: str = ""
    module: str = ""
    tags: List[str] = field(default_factory=list)
    enabled_by_default: bool = True
    registered_at: float = field(default_factory=time.time)


_TOOLS: Dict[str, ToolMeta] = {}
_RUNTIME_OVERRIDES: Dict[str, Optional[bool]] = {}


def register_tool(
    name: str,
    description: str = "",
    module: str = "",
    tags: Optional[List[str]] = None,
    enabled_by_default: bool = True,
) -> ToolMeta:
    """Register or update tool metadata."""
    if not name:
        raise ValueError("tool name is required")

    meta = _TOOLS.get(name)
    if meta is None:
        meta = ToolMeta(
            name=name,
            description=(description or "").strip(),
            module=(module or "").strip(),
            tags=list(tags or []),
            enabled_by_default=bool(enabled_by_default),
        )
        _TOOLS[name] = meta
        return meta

    # Merge updates (do not clobber existing info with empty values)
    if description and not meta.description:
        meta.description = description.strip()
    if module and not meta.module:
        meta.module = module.strip()
    if tags:
        merged = set(meta.tags)
        merged.update([t for t in tags if t])
        meta.tags = sorted(merged)
    meta.enabled_by_default = meta.enabled_by_default if meta.enabled_by_default is not None else bool(enabled_by_default)
    return meta


def _env_disabled_set() -> set[str]:
    return set(_parse_csv(os.getenv("TOOLS_DISABLED", "")))


def _env_enabled_only_set() -> set[str]:
    return set(_parse_csv(os.getenv("TOOLS_ENABLED_ONLY", "")))


def is_tool_enabled(name: str) -> bool:
    """Return whether a tool is enabled (runtime override > env > default)."""
    if not name:
        return True

    override = _RUNTIME_OVERRIDES.get(name)
    if override is not None:
        return bool(override)

    enabled_only = _env_enabled_only_set()
    if enabled_only:
        return name in enabled_only

    disabled = _env_disabled_set()
    if name in disabled:
        return False

    meta = _TOOLS.get(name)
    if meta is not None:
        return bool(meta.enabled_by_default)

    return True


def set_tool_enabled(name: str, enabled: bool) -> None:
    """Set runtime override for tool enabled state."""
    register_tool(name=name)
    _RUNTIME_OVERRIDES[name] = bool(enabled)


def reset_tool_overrides() -> None:
    """Clear all runtime overrides."""
    _RUNTIME_OVERRIDES.clear()


def list_tools() -> List[Dict[str, Any]]:
    """Return tools list with resolved enabled status."""
    items: List[Dict[str, Any]] = []
    for name in sorted(_TOOLS.keys()):
        meta = _TOOLS[name]
        row = asdict(meta)
        row["enabled"] = is_tool_enabled(name)
        row["runtime_override"] = _RUNTIME_OVERRIDES.get(name)
        items.append(row)
    return items


__all__ = [
    "ToolMeta",
    "register_tool",
    "is_tool_enabled",
    "set_tool_enabled",
    "reset_tool_overrides",
    "list_tools",
]

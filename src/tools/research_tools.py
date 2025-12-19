############################################################
# 📘 文件说明：
# 本文件实现的功能：MCP 相关模块：定义/封装工具调用并强化 stdout 协议安全。
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
# - 依赖（本地）：core.mcp_safety, skills.research.quant_research
#
# 🕒 创建时间：2025-12-19
############################################################

from __future__ import annotations

import json
from typing import Any, Iterable, List

from core.mcp_safety import mcp_tool_safe
from skills.research.quant_research import (
    execute_quant_research,
    generate_quant_prompts,
)


def _parse_sections(sections: str) -> List[str]:
    return [s.strip() for s in (sections or "").split(",") if s.strip()]


def register_tools(mcp: Any) -> None:
    @mcp.tool()
    @mcp_tool_safe
    def generate_quant_research_prompts(
        topic: str,
        focus: str = "balanced",
        sections: str = "",
    ) -> str:
        """
        生成量化研究提示词清单。
        Args:
            topic: 研究主题，例如“BTC/USDT”或“以太坊资金费率”。
            focus: 视角（balanced/alpha/risk/macro）。
            sections: 可选，指定 section id，逗号分隔。
        """
        prompts = generate_quant_prompts(
            topic=topic,
            focus=focus,
            sections=_parse_sections(sections),
        )
        return json.dumps(
            {"topic": topic, "focus": focus, "prompts": prompts},
            ensure_ascii=False,
            indent=2,
        )

    @mcp.tool()
    @mcp_tool_safe
    def run_quant_research(
        topic: str,
        focus: str = "balanced",
        sections: str = "",
        num_sources: int = 4,
        save_to_notion: bool = False,
        tags: str = "",
    ) -> str:
        """
        执行量化研究：批量调用 ai_research + 可选保存 Notion。
        Args:
            topic: 研究主题。
            focus: 视角（balanced/alpha/risk/macro）。
            sections: 限定 section id（可选）。
            num_sources: 每条 prompt 的来源数量。
            save_to_notion: 是否写入 Notion。
            tags: Notion 标签，逗号分隔。
        """
        result = execute_quant_research(
            topic=topic,
            focus=focus,
            sections=_parse_sections(sections),
            num_sources=num_sources,
            save_to_notion=save_to_notion,
            tags=[t.strip() for t in tags.split(",") if t.strip()],
        )
        return json.dumps(result, ensure_ascii=False, indent=2)


__all__ = ["register_tools"]

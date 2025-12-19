############################################################
# 📘 文件说明：
# 本文件实现的功能：Aggregate market quality score using structure + flow modules.
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
# - 依赖（标准库）：__future__, typing
# - 依赖（第三方）：无
# - 依赖（本地）：..data_provider, .flow_pressure, .structure_quality
#
# 🕒 创建时间：2025-12-19
############################################################

"""Aggregate market quality score using structure + flow modules."""

from __future__ import annotations

from typing import Any, Dict

from ..data_provider import StandardMarketData
from .structure_quality import analyze_structure_quality
from .flow_pressure import analyze_flow_pressure


def analyze_market_quality(data: StandardMarketData, params: Dict[str, Any]) -> Dict[str, Any]:
    structure = analyze_structure_quality(data, params)
    flow = analyze_flow_pressure(data, params)
    if "error" in structure or "error" in flow:
        return {"name": "market_quality", "error": "insufficient_data"}

    structure_score = structure.get("structure_alignment_score", 0.0)
    confidence = flow.get("confidence_pct", 0.0)
    pressure_state = flow.get("state", "balanced")

    quality = 0.5 * structure_score + 0.5 * confidence
    tradable = quality >= 55 and pressure_state != "balanced"
    note = "Focus on high conviction trends." if tradable else "Market quality mediocre, wait for clarity."

    return {
        "name": "market_quality",
        "structure_alignment_score": structure_score,
        "flow_confidence_pct": confidence,
        "pressure_state": pressure_state,
        "quality_score": round(quality, 2),
        "tradable": tradable,
        "note": note,
    }


__all__ = ["analyze_market_quality"]

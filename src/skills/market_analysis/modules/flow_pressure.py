############################################################
# 📘 文件说明：
# 本文件实现的功能：Order flow pressure analysis.
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
# - 依赖（第三方）：pandas
# - 依赖（本地）：..data_provider
#
# 🕒 创建时间：2025-12-19
############################################################

"""Order flow pressure analysis."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from ..data_provider import StandardMarketData


def analyze_flow_pressure(data: StandardMarketData, params: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate taker buy/sell pressure using volume + price response."""
    df = data.df.copy()
    if "flow_samples" in params:
        df = pd.DataFrame(params["flow_samples"], columns=df.columns)
    if df.empty or len(df) < 5:
        return {"name": "flow_pressure", "error": "not_enough_data"}

    df["mid_move"] = df["close"].pct_change().fillna(0)
    df["directional_volume"] = df["volume"] * df["mid_move"].apply(lambda x: 1 if x >= 0 else -1)
    pressure = df["directional_volume"].sum()
    total_volume = df["volume"].sum() or 1.0
    ratio = pressure / total_volume
    state = "buying" if ratio > 0.05 else "selling" if ratio < -0.05 else "balanced"

    volatility = float(df["mid_move"].std())
    conviction = min(abs(ratio) * 100, 100.0)

    markdown = (
        f"**Flow Pressure**\n"
        f"- 状态: {state}\n"
        f"- 压力比: {ratio:.2%}\n"
        f"- 波动率: {volatility:.4f}\n"
        f"- 置信度: {conviction:.1f}%\n"
    )

    return {
        "name": "flow_pressure",
        "state": state,
        "pressure_ratio": round(ratio, 4),
        "volatility": round(volatility, 4),
        "confidence_pct": round(conviction, 2),
        "markdown": markdown,
    }


__all__ = ["analyze_flow_pressure"]

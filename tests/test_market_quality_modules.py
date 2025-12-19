############################################################
# 📘 文件说明：
# 本文件实现的功能：测试用例：验证 test_market_quality_modules 相关逻辑的正确性与回归。
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
# - 依赖（标准库）：无
# - 依赖（第三方）：pandas
# - 依赖（本地）：skills.market_analysis.data_provider, skills.market_analysis.modules.flow_pressure, skills.market_analysis.modules.market_quality
#
# 🕒 创建时间：2025-12-19
############################################################

import pandas as pd

from skills.market_analysis.data_provider import StandardMarketData
from skills.market_analysis.modules.flow_pressure import analyze_flow_pressure
from skills.market_analysis.modules.market_quality import analyze_market_quality


def _sample_df():
    rows = []
    price = 100.0
    for idx in range(60):
        price += 0.3 if idx % 2 == 0 else -0.1
        rows.append([idx, price - 0.5, price + 0.5, price - 1, price, 50 + idx])
    return pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])


def test_flow_pressure_without_network():
    df = _sample_df()
    data = StandardMarketData(
        ohlcv=df.values.tolist(),
        ticker={"last": df["close"].iloc[-1]},
        df=df,
        metadata={"symbol": "BTC/USDT", "timeframe": "1h"},
    )
    payload = analyze_flow_pressure(data, {})
    assert payload["name"] == "flow_pressure"
    assert payload["state"] in {"buying", "selling", "balanced"}


def test_market_quality_combines_modules():
    df = _sample_df()
    data = StandardMarketData(
        ohlcv=df.values.tolist(),
        ticker={"last": df["close"].iloc[-1]},
        df=df,
        metadata={"symbol": "BTC/USDT", "timeframe": "1h"},
    )
    payload = analyze_market_quality(data, {"skip_fetch": True})
    assert payload["name"] == "market_quality"
    assert 0 <= payload["quality_score"] <= 100

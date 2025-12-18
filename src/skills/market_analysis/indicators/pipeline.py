############################################################
# 📘 文件说明：指标流水线
# 本文件实现的功能：技术指标的批量计算流水线
#
# 📋 程序整体伪代码（中文）：
# 1. 初始化依赖模块和配置
# 2. 定义核心类和函数
# 3. 实现主要业务逻辑
# 4. 提供对外接口
# 5. 异常处理与日志记录
#
# 🔄 程序流程图（逻辑流）：
# ┌──────────────┐
# │  输入数据    │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  核心处理逻辑 │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  输出结果    │
# └──────────────┘
#
# 📊 数据管道说明：
# 数据流向：交易所API → 数据处理 → 指标计算 → 分析结果输出
#
# 🧩 文件结构：
# - 函数: calculate_indicators
#
# 🔗 主要依赖：__future__, market_analysis, pandas
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

import pandas as pd

from .momentum_indicators import add_momentum_indicators
from .trend_indicators import add_trend_indicators
from .volatility_indicators import add_volatility_indicators
from .volume_indicators import add_volume_indicators


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = add_momentum_indicators(df)
    df = add_trend_indicators(df)
    df = add_volatility_indicators(df)
    df = add_volume_indicators(df)
    return df.bfill().ffill()

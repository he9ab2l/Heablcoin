############################################################
# 📘 文件说明：市场分析核心
# 本文件实现的功能：技术分析、情绪分析、信号生成的核心逻辑
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
# - 类: MarketAnalyzer
# - 函数: analyze
#
# 🔗 主要依赖：__future__, market_analysis, typing
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .data_provider import DataProvider
from .registry import AnalyzerRegistry
from .modules.technical_summary import analyze_technical_summary
from .modules.trading_signals import analyze_trading_signals
from .modules.sentiment import analyze_sentiment
from .modules.patterns import detect_patterns
from .modules.market_structure import analyze_structure
from .report_generator import to_json, to_markdown


class MarketAnalyzer:
    def __init__(self, provider: Optional[DataProvider] = None, registry: Optional[AnalyzerRegistry] = None) -> None:
        self.provider = provider or DataProvider.instance()
        self.registry = registry or AnalyzerRegistry()
        self._register_builtin_modules()

    def _register_builtin_modules(self) -> None:
        if self.registry.get("technical") is None:
            self.registry.register("technical", analyze_technical_summary, enabled_by_default=True)
        if self.registry.get("signals") is None:
            self.registry.register("signals", analyze_trading_signals, enabled_by_default=True)
        if self.registry.get("sentiment") is None:
            self.registry.register("sentiment", analyze_sentiment, enabled_by_default=False)
        if self.registry.get("patterns") is None:
            self.registry.register("patterns", detect_patterns, enabled_by_default=False)
        if self.registry.get("structure") is None:
            self.registry.register("structure", analyze_structure, enabled_by_default=False)

    def analyze(
        self,
        symbol: str = "BTC/USDT",
        timeframe: str = "1h",
        modules: Optional[List[str]] = None,
        limit: int = 100,
        return_format: str = "markdown",
        **params: Any,
    ) -> str:
        selected = modules or self.registry.defaults()
        std = self.provider.get_standard_data(symbol=symbol, timeframe=timeframe, limit=limit, include_ticker=True)

        out: List[Dict[str, Any]] = []
        for name in selected:
            mod = self.registry.get(name)
            if mod is None:
                out.append({"name": name, "error": "unknown_module"})
                continue
            try:
                out.append(mod.analyze(std, params))
            except Exception as e:
                out.append({"name": name, "error": f"{type(e).__name__}: {e}"})

        fmt = (return_format or "markdown").lower().strip()
        title = f"Market Analysis - {symbol} - {timeframe}"
        if fmt == "json":
            return to_json(title, out)
        return to_markdown(title, out)

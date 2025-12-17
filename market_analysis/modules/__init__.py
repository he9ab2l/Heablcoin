from __future__ import annotations

from market_analysis.modules.technical_summary import analyze_technical_summary
from market_analysis.modules.trading_signals import analyze_trading_signals
from market_analysis.modules.sentiment import analyze_sentiment
from market_analysis.modules.patterns import detect_patterns
from market_analysis.modules.market_structure import analyze_structure

__all__ = [
    "analyze_technical_summary",
    "analyze_trading_signals",
    "analyze_sentiment",
    "detect_patterns",
    "analyze_structure",
]

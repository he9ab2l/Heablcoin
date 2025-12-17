from __future__ import annotations

from personal_analytics.modules.performance import analyze_performance
from personal_analytics.modules.risk import analyze_risk
from personal_analytics.modules.attribution import analyze_attribution
from personal_analytics.modules.trading_behavior import analyze_behavior
from personal_analytics.modules.portfolio import analyze_portfolio
from personal_analytics.modules.cost_analysis import analyze_costs
from personal_analytics.modules.period_stats import analyze_periods
from personal_analytics.modules.session_analysis import analyze_sessions
from personal_analytics.modules.trade_journal import analyze_journal, add_trade_note, search_trades
from personal_analytics.modules.funds_flow import analyze_funds, add_funds_record

__all__ = [
    "analyze_performance",
    "analyze_risk",
    "analyze_attribution",
    "analyze_behavior",
    "analyze_portfolio",
    "analyze_costs",
    "analyze_periods",
    "analyze_sessions",
    "analyze_journal",
    "analyze_funds",
    "add_trade_note",
    "add_funds_record",
    "search_trades",
]

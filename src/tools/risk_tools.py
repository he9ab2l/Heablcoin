"""MCP tools exposing risk governance primitives."""


from __future__ import annotations


import json

from typing import Any


from core.mcp_safety import mcp_tool_safe

from skills.risk import (

    RiskBudgetManager,

    FundAllocator,

    VolatilityPositionSizer,

    CircuitBreaker,

)


def register_tools(mcp: Any) -> None:

    budget_manager = RiskBudgetManager()

    allocator = FundAllocator()

    sizer = VolatilityPositionSizer()

    circuit_breaker = CircuitBreaker()


    # ------------------------------------------------------------------ budget tools

    @mcp.tool()

    @mcp_tool_safe

    def get_risk_budget_status() -> str:

        """获取每日/每周/每月风险预算及冻结状态。"""

        status = budget_manager.get_status()

        return json.dumps(status, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def record_risk_event(loss_amount: float, tag: str = "", note: str = "") -> str:

        """记录一笔亏损事件并刷新预算使用情况。"""

        result = budget_manager.record_event(loss_amount=abs(loss_amount), tag=tag, note=note)

        return json.dumps(result, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def update_risk_budget(period: str, budget: float, unfreeze: bool = False) -> str:

        """更新指定周期的预算 (daily/weekly/monthly)。"""

        status = budget_manager.update_budget(period=period.lower(), budget=budget, unfreeze=unfreeze)

        return json.dumps(status, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def reset_risk_period(period: str) -> str:

        """手动重置指定周期的预算统计。"""

        status = budget_manager.reset_period(period.lower())

        return json.dumps(status, ensure_ascii=False, indent=2)


    # ------------------------------------------------------------------ capital pools

    @mcp.tool()

    @mcp_tool_safe

    def set_strategy_pool(name: str, capital: float, max_drawdown_pct: float = 0.2, notes: str = "") -> str:

        """设置或调整某个策略的独立资金池。"""

        payload = allocator.set_pool(name=name, capital=capital, max_drawdown_pct=max_drawdown_pct, notes=notes)

        return json.dumps(payload, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def allocate_strategy_capital(name: str, amount: float) -> str:

        """占用策略资金池中的资金（开仓前调用）。"""

        payload = allocator.allocate(name=name, amount=amount)

        return json.dumps(payload, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def release_strategy_capital(name: str, amount: float, realized_pnl: float = 0.0) -> str:

        """释放已用资金并同步实盘盈亏。"""

        payload = allocator.release(name=name, amount=amount, realized_pnl=realized_pnl)

        return json.dumps(payload, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def list_strategy_pools() -> str:

        """查看全部策略资金池状态。"""

        payload = allocator.list_pools()

        return json.dumps(payload, ensure_ascii=False, indent=2)


    # ------------------------------------------------------------------ volatility sizing

    @mcp.tool()

    @mcp_tool_safe

    def suggest_vol_adjusted_notional(

        account_balance: float,

        risk_pct: float,

        symbol: str = "BTC/USDT",

        timeframe: str = "1h",

        target_vol: float = 0.02,

        lookback: int = 120,

    ) -> str:

        """按照实时波动率自动缩放仓位规模。"""

        result = sizer.suggest_notional(

            account_balance=account_balance,

            risk_pct=risk_pct,

            symbol=symbol,

            timeframe=timeframe,

            target_vol=target_vol,

            lookback=lookback,

        )

        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)


    # ------------------------------------------------------------------ circuit breaker

    @mcp.tool()

    @mcp_tool_safe

    def configure_circuit_breaker(symbol: str, threshold_pct: float = 0.05, cooldown_minutes: int = 30) -> str:

        """配置指定交易对的熔断阈值。"""

        payload = circuit_breaker.configure(symbol=symbol, threshold_pct=threshold_pct, cooldown_minutes=cooldown_minutes)

        return json.dumps(payload, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def check_circuit_breaker(symbol: str, move_pct: float, liquidity_score: float = 1.0, reason: str = "") -> str:

        """检查是否触发熔断，并更新最新行情样本。"""

        payload = circuit_breaker.check_move(

            symbol=symbol,

            move_pct=move_pct,

            liquidity_score=liquidity_score,

            reason=reason,

        )

        return json.dumps(payload, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def circuit_breaker_status(symbol: str = "") -> str:

        """查看某个交易对或全部熔断状态。"""

        payload = circuit_breaker.status(symbol or None)

        return json.dumps(payload, ensure_ascii=False, indent=2)


__all__ = ["register_tools"]

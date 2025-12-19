from __future__ import annotations
from typing import Any, List, Optional
from core.mcp_safety import mcp_tool_safe
from skills.personal_analytics.core import PersonalAnalyzer
from skills.personal_analytics.modules.trade_journal import add_trade_note, search_trades
from skills.personal_analytics.modules.funds_flow import add_funds_record
from skills.personal_analytics.data_provider import read_trade_history
from skills.report.query_backup import save_query_backup


def register_tools(mcp: Any) -> None:
    """注册个人分析 MCP 工具"""
    @mcp.tool()
    @mcp_tool_safe
    def get_personal_analysis(
        modules: str = "",
        limit: int = 0,
        initial_capital: float = 10000.0,
        return_format: str = "markdown",
    ) -> str:
        """
        获取个人交易分析报告。
        Args:
            modules: 要执行的模块，逗号分隔，可选:
                - performance: 绩效分析 (ROI、胜率、夏普比率)
                - risk: 风险分析 (最大回撤、连续亏损)
                - attribution: 盈亏归因 (按币种/方向/时间)
                - behavior: 交易行为分析
                - portfolio: 投资组合分析 (持仓、浮盈)
                - costs: 交易成本分析 (手续费)
                - periods: 周期性统计 (日/周/月收益)
                - sessions: 交易时段分析 (亚欧美盘)
                - journal: 交易复盘
                - funds: 出入金分析
                留空则执行默认模块 (performance,risk,portfolio,attribution)
            limit: 限制分析的交易记录数量，0 表示全部
            initial_capital: 初始资金 (USDT)，用于计算回撤等指标
            return_format: 返回格式 "markdown" 或 "json"
        Returns:
            个人交易分析报告
        """
        analyzer = PersonalAnalyzer()
        # 解析模块列表
        module_list: Optional[List[str]] = None
        if modules and modules.strip():
            module_list = [m.strip() for m in modules.split(",") if m.strip()]
        # 解析 limit
        limit_val = int(limit) if limit and int(limit) > 0 else None
        result = analyzer.analyze(
            modules=module_list,
            limit=limit_val,
            initial_capital=float(initial_capital),
            return_format=return_format,
        )
        try:
            save_query_backup(
                tool_name="get_personal_analysis",
                title="personal_analysis",
                content=result,
                params={
                    "modules": modules,
                    "limit": limit,
                    "initial_capital": initial_capital,
                    "return_format": return_format,
                },
                return_format=return_format,
                extra_meta={"kind": "personal_analytics"},
            )
        except Exception:
            pass
        return result
    @mcp.tool()
    @mcp_tool_safe
    def get_full_personal_analysis(
        initial_capital: float = 10000.0,
        return_format: str = "markdown",
    ) -> str:
        """
        获取完整的个人交易分析报告（所有模块）。
        Args:
            initial_capital: 初始资金 (USDT)
            return_format: 返回格式 "markdown" 或 "json"
        Returns:
            完整的个人交易分析报告
        """
        analyzer = PersonalAnalyzer()
        result = analyzer.analyze(
            modules=PersonalAnalyzer.ALL_MODULES,
            initial_capital=float(initial_capital),
            return_format=return_format,
        )
        try:
            save_query_backup(
                tool_name="get_full_personal_analysis",
                title="full_personal_analysis",
                content=result,
                params={"initial_capital": initial_capital, "return_format": return_format},
                return_format=return_format,
                extra_meta={"kind": "personal_analytics"},
            )
        except Exception:
            pass
        return result
    @mcp.tool()
    @mcp_tool_safe
    def get_portfolio_analysis(return_format: str = "markdown") -> str:
        """
        获取投资组合与持仓分析。
        包括：资产总览、持仓分布、平均成本、未实现盈亏。
        Args:
            return_format: 返回格式 "markdown" 或 "json"
        Returns:
            投资组合分析报告
        """
        analyzer = PersonalAnalyzer()
        return analyzer.analyze(
            modules=["portfolio"],
            return_format=return_format,
        )
    @mcp.tool()
    @mcp_tool_safe
    def get_period_performance(
        period: str = "all",
        return_format: str = "markdown",
    ) -> str:
        """
        获取周期性绩效统计。
        Args:
            period: 统计周期，可选 "daily", "weekly", "monthly", "all"
            return_format: 返回格式 "markdown" 或 "json"
        Returns:
            周期性绩效统计
        """
        analyzer = PersonalAnalyzer()
        return analyzer.analyze(
            modules=["periods", "performance"],
            return_format=return_format,
        )
    @mcp.tool()
    @mcp_tool_safe
    def get_trading_session_analysis(return_format: str = "markdown") -> str:
        """
        获取交易时段分析。
        分析亚洲盘、欧洲盘、美洲盘的交易绩效差异。
        Args:
            return_format: 返回格式 "markdown" 或 "json"
        Returns:
            交易时段分析报告
        """
        analyzer = PersonalAnalyzer()
        return analyzer.analyze(
            modules=["sessions"],
            return_format=return_format,
        )
    @mcp.tool()
    @mcp_tool_safe
    def get_cost_analysis(return_format: str = "markdown") -> str:
        """
        获取交易成本分析。
        汇总手续费、资金费率等，分析成本对盈亏的影响。
        Args:
            return_format: 返回格式 "markdown" 或 "json"
        Returns:
            交易成本分析报告
        """
        analyzer = PersonalAnalyzer()
        return analyzer.analyze(
            modules=["costs"],
            return_format=return_format,
        )
    @mcp.tool()
    @mcp_tool_safe
    def add_trade_journal_note(
        order_id: str,
        note: str,
        tags: str = "",
    ) -> str:
        """
        为交易添加复盘笔记。
        Args:
            order_id: 订单ID
            note: 笔记内容（交易理由、心得、错误总结等）
            tags: 标签，逗号分隔（如 "错误,止损,成功"）
        Returns:
            保存结果
        """
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        result = add_trade_note(order_id, note, tag_list)
        if result.get("success"):
            return f"✅ 笔记已保存: {order_id}"
        return f"❌ 保存失败: {result.get('message', '')}"
    @mcp.tool()
    @mcp_tool_safe
    def record_funds_flow(
        amount: float,
        record_type: str,
        currency: str = "USDT",
        note: str = "",
        date: str = "",
    ) -> str:
        """
        记录出入金。
        Args:
            amount: 金额（正数）
            record_type: 类型 "deposit" (入金) 或 "withdraw" (出金)
            currency: 币种，默认 USDT
            note: 备注
            date: 日期 (YYYY-MM-DD)，留空则为今天
        Returns:
            记录结果
        """
        result = add_funds_record(
            amount=float(amount),
            record_type=record_type,
            currency=currency,
            note=note,
            date=date if date else None,
        )
        if result.get("success"):
            r = result.get("record", {})
            return f"✅ 已记录: {r.get('type', '').upper()} {r.get('amount', 0):,.2f} {r.get('currency', 'USDT')} ({r.get('date', '')})"
        return f"❌ 记录失败: {result.get('message', '')}"
    @mcp.tool()
    @mcp_tool_safe
    def search_trade_history(
        symbol: str = "",
        side: str = "",
        start_date: str = "",
        end_date: str = "",
        limit: int = 20,
    ) -> str:
        """
        搜索交易历史记录。
        Args:
            symbol: 交易对筛选（如 BTC, ETH）
            side: 方向筛选 (BUY/SELL)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            limit: 返回数量限制
        Returns:
            符合条件的交易记录
        """
        trades = read_trade_history()
        results = search_trades(
            trades,
            symbol=symbol if symbol else None,
            side=side if side else None,
            start_date=start_date if start_date else None,
            end_date=end_date if end_date else None,
        )
        # 限制数量
        results = results[:int(limit)] if limit else results[:20]
        if not results:
            return "未找到符合条件的交易记录"
        lines = [f"# 搜索结果 ({len(results)} 条)\n"]
        for r in results:
            sym = r.get("symbol") or r.get("交易对") or ""
            s = r.get("side") or r.get("方向") or ""
            qty = r.get("qty") or r.get("数量") or 0
            price = r.get("price") or r.get("价格") or 0
            t = r.get("time") or r.get("时间") or ""
            lines.append(f"- {t} | {sym} | {s} {float(qty):.6f} @ ${float(price):,.4f}")
        return "\n".join(lines)
    @mcp.tool()
    @mcp_tool_safe
    def list_personal_analysis_modules() -> str:
        """列出所有可用的个人分析模块"""
        modules = PersonalAnalyzer.list_modules()
        lines = ["# 可用的个人分析模块\n"]
        for m in modules:
            lines.append(f"- **{m['name']}**: {m['title']} - {m['description']}")
        lines.append("\n## 默认模块")
        lines.append(", ".join(PersonalAnalyzer.DEFAULT_MODULES))
        lines.append("\n## 全部模块")
        lines.append(", ".join(PersonalAnalyzer.ALL_MODULES))
        return "\n".join(lines)
__all__ = ["register_tools"]

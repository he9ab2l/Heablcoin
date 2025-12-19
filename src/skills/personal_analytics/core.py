from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from .data_provider import read_trade_history
from .modules.performance import analyze_performance
from .modules.risk import analyze_risk
from .modules.attribution import analyze_attribution
from .modules.trading_behavior import analyze_behavior
from .modules.portfolio import analyze_portfolio
from .modules.cost_analysis import analyze_costs
from .modules.period_stats import analyze_periods
from .modules.session_analysis import analyze_sessions
from .modules.trade_journal import analyze_journal
from .modules.funds_flow import analyze_funds


class PersonalAnalyzer:
    """个人交易分析器"""
    AVAILABLE_MODULES = {
        "performance": analyze_performance,
        "risk": analyze_risk,
        "attribution": analyze_attribution,
        "behavior": analyze_behavior,
        "portfolio": analyze_portfolio,
        "costs": analyze_costs,
        "periods": analyze_periods,
        "sessions": analyze_sessions,
        "journal": analyze_journal,
        "funds": analyze_funds,
    }
    DEFAULT_MODULES = ["performance", "risk", "portfolio", "attribution"]
    ALL_MODULES = [
        "performance", "risk", "attribution", "behavior",
        "portfolio", "costs", "periods", "sessions", "journal", "funds"
    ]
    def __init__(self) -> None:
        pass
    def analyze(
        self,
        modules: Optional[List[str]] = None,
        limit: Optional[int] = None,
        initial_capital: float = 10000.0,
        return_format: str = "markdown",
        **params: Any,
    ) -> str:
        """
        执行个人交易分析。
        Args:
            modules: 要执行的分析模块列表，默认全部
            limit: 限制分析的交易记录数量
            initial_capital: 初始资金（用于计算回撤等）
            return_format: 返回格式 "markdown" 或 "json"
            **params: 传递给各模块的额外参数
        Returns:
            分析结果（markdown 或 JSON 格式）
        """
        # 读取交易历史
        trades = read_trade_history(limit=limit)
        # 确定要执行的模块
        selected = modules or self.DEFAULT_MODULES
        # 准备参数
        analysis_params = {
            "initial_capital": initial_capital,
            **params,
        }
        # 执行分析
        results: List[Dict[str, Any]] = []
        for name in selected:
            if name not in self.AVAILABLE_MODULES:
                results.append({"name": name, "error": "unknown_module"})
                continue
            try:
                result = self.AVAILABLE_MODULES[name](trades, analysis_params)
                results.append(result)
            except Exception as e:
                results.append({"name": name, "error": f"{type(e).__name__}: {e}"})
        # 格式化输出
        fmt = (return_format or "markdown").lower().strip()
        if fmt == "json":
            return self._to_json(results)
        return self._to_markdown(results)
    def _to_markdown(self, results: List[Dict[str, Any]]) -> str:
        """将结果转换为 Markdown 格式"""
        parts = [
            "# 📊 个人交易分析报告\n",
            f"{'═' * 40}\n\n",
        ]
        for r in results:
            if "error" in r:
                parts.append(f"## ❌ {r.get('name', 'unknown')}\n\n错误: {r['error']}\n\n")
            elif "markdown" in r:
                parts.append(r["markdown"])
                parts.append("\n\n")
            else:
                parts.append(f"## {r.get('name', 'unknown')}\n\n{json.dumps(r.get('payload', {}), ensure_ascii=False, indent=2)}\n\n")
        return "".join(parts)
    def _to_json(self, results: List[Dict[str, Any]]) -> str:
        """将结果转换为 JSON 格式"""
        output = {
            "title": "个人交易分析报告",
            "modules": {},
        }
        for r in results:
            name = r.get("name", "unknown")
            if "error" in r:
                output["modules"][name] = {"error": r["error"]}
            else:
                output["modules"][name] = r.get("payload", {})
        return json.dumps(output, ensure_ascii=False, indent=2)
    @classmethod
    def list_modules(cls) -> List[Dict[str, str]]:
        """列出所有可用模块"""
        from .modules.performance import get_module_info as perf_info
        from .modules.risk import get_module_info as risk_info
        from .modules.attribution import get_module_info as attr_info
        from .modules.trading_behavior import get_module_info as behav_info
        from .modules.portfolio import get_module_info as port_info
        from .modules.cost_analysis import get_module_info as cost_info
        from .modules.period_stats import get_module_info as period_info
        from .modules.session_analysis import get_module_info as sess_info
        from .modules.trade_journal import get_module_info as journal_info
        from .modules.funds_flow import get_module_info as funds_info


        return [
            perf_info(), risk_info(), attr_info(), behav_info(),
            port_info(), cost_info(), period_info(), sess_info(),
            journal_info(), funds_info(),
        ]
__all__ = ["PersonalAnalyzer"]

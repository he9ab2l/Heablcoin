############################################################
# 📘 文件说明：
# 本文件实现的功能：交易行为与心理分析模块
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
# - 依赖（标准库）：__future__, datetime, json, typing
# - 依赖（第三方）：无
# - 依赖（本地）：core.orchestration.ai_roles, utils.smart_logger
#
# 🕒 创建时间：2025-12-19
############################################################

"""
交易行为与心理分析模块
======================
分析交易者的行为模式、心理状态和决策质量。
使用 ai_memory 和 ai_reasoning 角色进行深度分析。
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from core.orchestration.ai_roles import remember, reason, call_ai, AIRole
from utils.smart_logger import get_logger

logger = get_logger("behavior")


class BehaviorAnalyzer:
    """交易行为分析器"""
    
    def __init__(self):
        self.logger = logger
    
    def analyze_trading_pattern(self, trade_history: List[Dict]) -> Dict[str, Any]:
        """
        分析交易模式
        
        Args:
            trade_history: 交易历史记录列表
        
        Returns:
            Dict: 交易模式分析结果
        """
        try:
            if not trade_history:
                return {
                    "success": False,
                    "error": "No trade history provided"
                }
            
            # 将交易历史转换为文本
            history_text = "\n".join([
                f"时间: {t.get('timestamp', 'N/A')}, "
                f"交易对: {t.get('symbol', 'N/A')}, "
                f"方向: {t.get('side', 'N/A')}, "
                f"数量: {t.get('amount', 0)}, "
                f"价格: {t.get('price', 0)}, "
                f"盈亏: {t.get('pnl', 0)}"
                for t in trade_history[-50:]  # 最近50笔
            ])
            
            # 使用 AI 记忆角色分析长期模式
            pattern_prompt = f"""
分析以下交易历史，识别交易模式和习惯：

{history_text}

请识别：
1. 交易频率模式（高频/中频/低频）
2. 偏好的交易时段
3. 常交易的币种
4. 持仓时间偏好（短线/中线/长线）
5. 风险偏好（激进/稳健/保守）
6. 决策模式（冲动/理性/混合）

以 JSON 格式输出。
"""
            
            response = remember(pattern_prompt, documents=[history_text])
            
            if not response.success:
                return {
                    "success": False,
                    "error": response.error
                }
            
            pattern_data = response.parsed or {}
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "total_trades_analyzed": len(trade_history),
                "trading_frequency": pattern_data.get("trading_frequency", "unknown"),
                "preferred_time": pattern_data.get("preferred_time", "unknown"),
                "favorite_symbols": pattern_data.get("favorite_symbols", []),
                "holding_period": pattern_data.get("holding_period", "unknown"),
                "risk_preference": pattern_data.get("risk_preference", "unknown"),
                "decision_pattern": pattern_data.get("decision_pattern", "unknown"),
                "raw_analysis": response.content
            }
            
        except Exception as e:
            logger.error(f"Trading pattern analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_psychological_state(self, recent_trades: List[Dict]) -> Dict[str, Any]:
        """
        分析心理状态
        
        Args:
            recent_trades: 最近的交易记录
        
        Returns:
            Dict: 心理状态分析
        """
        try:
            if not recent_trades:
                return {
                    "success": False,
                    "error": "No recent trades provided"
                }
            
            # 分析最近交易的盈亏情况
            wins = [t for t in recent_trades if t.get('pnl', 0) > 0]
            losses = [t for t in recent_trades if t.get('pnl', 0) < 0]
            
            win_rate = len(wins) / len(recent_trades) if recent_trades else 0
            avg_win = sum(t.get('pnl', 0) for t in wins) / len(wins) if wins else 0
            avg_loss = sum(t.get('pnl', 0) for t in losses) / len(losses) if losses else 0
            
            # 构建心理分析提示
            psych_prompt = f"""
基于以下交易数据，分析交易者的心理状态：

总交易数: {len(recent_trades)}
胜率: {win_rate:.1%}
平均盈利: {avg_win:.2f}
平均亏损: {avg_loss:.2f}

最近交易序列：
{json.dumps([{"symbol": t.get("symbol"), "side": t.get("side"), "pnl": t.get("pnl")} for t in recent_trades[-10:]], ensure_ascii=False, indent=2)}

请分析：
1. 当前情绪状态（恐惧/贪婪/冷静/焦虑）
2. 是否存在报复性交易
3. 是否存在过度自信
4. 是否存在损失厌恶
5. 纪律性评分（0-100）
6. 心理健康建议

以 JSON 格式输出。
"""
            
            response = reason(psych_prompt)
            
            if not response.success:
                return {
                    "success": False,
                    "error": response.error
                }
            
            psych_data = response.parsed or {}
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "trades_analyzed": len(recent_trades),
                "win_rate": f"{win_rate:.1%}",
                "emotional_state": psych_data.get("emotional_state", "unknown"),
                "revenge_trading": psych_data.get("revenge_trading", False),
                "overconfidence": psych_data.get("overconfidence", False),
                "loss_aversion": psych_data.get("loss_aversion", False),
                "discipline_score": psych_data.get("discipline_score", 50),
                "recommendations": psych_data.get("recommendations", []),
                "raw_analysis": response.content
            }
            
        except Exception as e:
            logger.error(f"Psychological analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_decision_quality(self, trade: Dict, market_context: Dict) -> Dict[str, Any]:
        """
        分析单笔交易的决策质量
        
        Args:
            trade: 交易记录
            market_context: 市场上下文（当时的行情数据）
        
        Returns:
            Dict: 决策质量分析
        """
        try:
            # 构建决策审查提示
            critique_prompt = f"""
审查以下交易决策的质量：

交易信息：
- 交易对: {trade.get('symbol')}
- 方向: {trade.get('side')}
- 价格: {trade.get('price')}
- 数量: {trade.get('amount')}
- 时间: {trade.get('timestamp')}
- 结果: {trade.get('pnl', 0)}

市场背景：
{json.dumps(market_context, ensure_ascii=False, indent=2)}

请评估：
1. 决策时机是否合理
2. 仓位大小是否适当
3. 是否符合风险管理原则
4. 决策依据是否充分
5. 决策质量评分（0-100）
6. 改进建议

以 JSON 格式输出。
"""
            
            from core.orchestration.ai_roles import critique
            
            response = critique(critique_prompt, criteria=["时机", "仓位", "风险", "依据"])
            
            if not response.success:
                return {
                    "success": False,
                    "error": response.error
                }
            
            quality_data = response.parsed or {}
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "trade_symbol": trade.get('symbol'),
                "timing_score": quality_data.get("timing_score", 50),
                "position_size_score": quality_data.get("position_size_score", 50),
                "risk_management_score": quality_data.get("risk_management_score", 50),
                "rationale_score": quality_data.get("rationale_score", 50),
                "overall_quality": quality_data.get("overall_quality", 50),
                "improvements": quality_data.get("improvements", []),
                "raw_critique": response.content
            }
            
        except Exception as e:
            logger.error(f"Decision quality analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_behavior_report(self, trade_history: List[Dict]) -> Dict[str, Any]:
        """
        生成完整的行为分析报告
        
        Args:
            trade_history: 完整交易历史
        
        Returns:
            Dict: 行为分析报告
        """
        try:
            # 分析交易模式
            pattern_analysis = self.analyze_trading_pattern(trade_history)
            
            # 分析心理状态（最近30笔）
            recent_trades = trade_history[-30:] if len(trade_history) > 30 else trade_history
            psych_analysis = self.analyze_psychological_state(recent_trades)
            
            # 生成综合报告
            report_prompt = f"""
基于以下分析，生成交易行为综合报告：

交易模式分析：
{json.dumps(pattern_analysis, ensure_ascii=False, indent=2)}

心理状态分析：
{json.dumps(psych_analysis, ensure_ascii=False, indent=2)}

请提供：
1. 行为特征总结
2. 优势和劣势
3. 主要问题识别
4. 改进建议（具体可执行）
5. 学习重点
6. 下一步行动计划

以 Markdown 格式输出完整报告。
"""
            
            from core.orchestration.ai_roles import write
            
            response = write(report_prompt, context={"tone": "professional"})
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "trades_analyzed": len(trade_history),
                "pattern_analysis": pattern_analysis,
                "psychological_analysis": psych_analysis,
                "comprehensive_report": response.content if response.success else "报告生成失败",
                "report_endpoint": response.endpoint if response.success else None
            }
            
        except Exception as e:
            logger.error(f"Behavior report generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 全局实例
_behavior_analyzer: Optional[BehaviorAnalyzer] = None


def get_behavior_analyzer() -> BehaviorAnalyzer:
    """获取全局行为分析器实例"""
    global _behavior_analyzer
    if _behavior_analyzer is None:
        _behavior_analyzer = BehaviorAnalyzer()
    return _behavior_analyzer

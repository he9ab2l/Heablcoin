############################################################
# 📘 文件说明：
# 本文件实现的功能：基本面分析模块
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
基本面分析模块
==============
负责分析市场基本面信息，包括新闻、公告、链上数据等。
使用 ai_research 角色获取和分析信息。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.orchestration.ai_roles import research, call_ai, AIRole
from utils.smart_logger import get_logger

logger = get_logger("fundamental")


class FundamentalAnalyzer:
    """基本面分析器"""
    
    def __init__(self):
        self.logger = logger
    
    def analyze_news(self, symbol: str, num_sources: int = 5) -> Dict[str, Any]:
        """
        分析新闻和市场情绪
        
        Args:
            symbol: 交易对符号
            num_sources: 新闻来源数量
        
        Returns:
            Dict: 新闻分析结果
        """
        try:
            # 构建搜索查询
            query = f"{symbol} cryptocurrency news latest market sentiment"
            
            # 使用 AI 研究角色获取新闻
            response = research(query, num_sources=num_sources)
            
            if not response.success:
                return {
                    "success": False,
                    "error": response.error,
                    "symbol": symbol
                }
            
            # 解析新闻数据
            news_data = response.parsed or {}
            
            # 使用 AI 推理角色分析情绪
            sentiment_prompt = f"""
分析以下关于 {symbol} 的新闻内容，评估市场情绪：

{response.content}

请提供：
1. 整体情绪评分（0-100，0=极度悲观，100=极度乐观）
2. 主要利好因素
3. 主要利空因素
4. 短期影响预测
5. 建议操作

以 JSON 格式输出。
"""
            
            sentiment_response = call_ai(
                role=AIRole.REASONING,
                prompt=sentiment_prompt,
                max_tokens=1024,
                temperature=0.3
            )
            
            sentiment_analysis = sentiment_response.parsed or {}
            
            return {
                "success": True,
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "news_sources": num_sources,
                "raw_news": response.content,
                "sentiment_score": sentiment_analysis.get("sentiment_score", 50),
                "bullish_factors": sentiment_analysis.get("bullish_factors", []),
                "bearish_factors": sentiment_analysis.get("bearish_factors", []),
                "short_term_impact": sentiment_analysis.get("short_term_impact", "neutral"),
                "recommendation": sentiment_analysis.get("recommendation", "hold"),
                "analysis_endpoint": response.endpoint
            }
            
        except Exception as e:
            logger.error(f"News analysis failed for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }
    
    def analyze_on_chain(self, symbol: str) -> Dict[str, Any]:
        """
        分析链上数据
        
        Args:
            symbol: 交易对符号
        
        Returns:
            Dict: 链上数据分析结果
        """
        try:
            # 构建查询
            query = f"{symbol} on-chain metrics whale activity network activity"
            
            # 获取链上数据信息
            response = research(query, num_sources=3)
            
            if not response.success:
                return {
                    "success": False,
                    "error": response.error,
                    "symbol": symbol
                }
            
            # 分析链上指标
            analysis_prompt = f"""
分析以下关于 {symbol} 的链上数据：

{response.content}

请评估：
1. 巨鲸活动情况
2. 网络活跃度
3. 交易所流入流出
4. 持币地址变化
5. 链上信号（看涨/看跌）

以 JSON 格式输出。
"""
            
            analysis_response = call_ai(
                role=AIRole.REASONING,
                prompt=analysis_prompt,
                max_tokens=1024,
                temperature=0.3
            )
            
            on_chain_data = analysis_response.parsed or {}
            
            return {
                "success": True,
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "whale_activity": on_chain_data.get("whale_activity", "unknown"),
                "network_activity": on_chain_data.get("network_activity", "unknown"),
                "exchange_flow": on_chain_data.get("exchange_flow", "unknown"),
                "address_change": on_chain_data.get("address_change", "unknown"),
                "on_chain_signal": on_chain_data.get("on_chain_signal", "neutral"),
                "raw_data": response.content
            }
            
        except Exception as e:
            logger.error(f"On-chain analysis failed for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }
    
    def get_market_events(self, symbol: str) -> Dict[str, Any]:
        """
        获取市场重大事件
        
        Args:
            symbol: 交易对符号
        
        Returns:
            Dict: 市场事件信息
        """
        try:
            query = f"{symbol} major events announcements partnerships regulations"
            
            response = research(query, num_sources=5)
            
            if not response.success:
                return {
                    "success": False,
                    "error": response.error,
                    "symbol": symbol
                }
            
            # 提取和分类事件
            events_prompt = f"""
从以下信息中提取关于 {symbol} 的重大事件：

{response.content}

请分类为：
1. 技术更新/升级
2. 合作伙伴关系
3. 监管消息
4. 市场动态
5. 其他重要事件

每个事件包含：时间、类型、描述、影响评估（正面/负面/中性）

以 JSON 格式输出。
"""
            
            events_response = call_ai(
                role=AIRole.REASONING,
                prompt=events_prompt,
                max_tokens=1536,
                temperature=0.3
            )
            
            events_data = events_response.parsed or {}
            
            return {
                "success": True,
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "events": events_data.get("events", []),
                "overall_impact": events_data.get("overall_impact", "neutral"),
                "raw_info": response.content
            }
            
        except Exception as e:
            logger.error(f"Market events analysis failed for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }
    
    def comprehensive_fundamental_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        综合基本面分析
        
        Args:
            symbol: 交易对符号
        
        Returns:
            Dict: 综合分析结果
        """
        try:
            # 并行获取各类信息
            news_analysis = self.analyze_news(symbol)
            on_chain_analysis = self.analyze_on_chain(symbol)
            market_events = self.get_market_events(symbol)
            
            # 综合评估
            综合_prompt = f"""
基于以下三个维度的分析，给出 {symbol} 的综合基本面评估：

1. 新闻情绪分析：
{json.dumps(news_analysis, ensure_ascii=False, indent=2)}

2. 链上数据分析：
{json.dumps(on_chain_analysis, ensure_ascii=False, indent=2)}

3. 市场事件分析：
{json.dumps(market_events, ensure_ascii=False, indent=2)}

请提供：
1. 综合评分（0-100）
2. 基本面强度（强/中/弱）
3. 主要驱动因素
4. 风险因素
5. 投资建议（强烈买入/买入/持有/卖出/强烈卖出）
6. 时间框架建议（短期/中期/长期）

以 JSON 格式输出。
"""
            
            comprehensive_response = call_ai(
                role=AIRole.REASONING,
                prompt=综合_prompt,
                max_tokens=1536,
                temperature=0.3
            )
            
            comprehensive_data = comprehensive_response.parsed or {}
            
            return {
                "success": True,
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "comprehensive_score": comprehensive_data.get("comprehensive_score", 50),
                "fundamental_strength": comprehensive_data.get("fundamental_strength", "medium"),
                "key_drivers": comprehensive_data.get("key_drivers", []),
                "risk_factors": comprehensive_data.get("risk_factors", []),
                "recommendation": comprehensive_data.get("recommendation", "hold"),
                "timeframe": comprehensive_data.get("timeframe", "medium-term"),
                "components": {
                    "news": news_analysis,
                    "on_chain": on_chain_analysis,
                    "events": market_events
                }
            }
            
        except Exception as e:
            logger.error(f"Comprehensive fundamental analysis failed for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }


# 全局实例
_fundamental_analyzer: Optional[FundamentalAnalyzer] = None


def get_fundamental_analyzer() -> FundamentalAnalyzer:
    """获取全局基本面分析器实例"""
    global _fundamental_analyzer
    if _fundamental_analyzer is None:
        _fundamental_analyzer = FundamentalAnalyzer()
    return _fundamental_analyzer

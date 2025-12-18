############################################################
# 📘 文件说明：分析注册表
# 本文件实现的功能：分析模块的配置和指标注册
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
# - 类: AnalyzerModule, AnalyzerRegistry
# - 函数: register, get, list, defaults
#
# 🔗 主要依赖：__future__, dataclasses, market_analysis, typing
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .data_provider import StandardMarketData


AnalyzerFn = Callable[[StandardMarketData, Dict[str, Any]], Dict[str, Any]]


@dataclass
class AnalyzerModule:
    name: str
    analyze: AnalyzerFn
    enabled_by_default: bool = True


class AnalyzerRegistry:
    def __init__(self) -> None:
        self._modules: Dict[str, AnalyzerModule] = {}

    def register(self, name: str, analyze: AnalyzerFn, enabled_by_default: bool = True) -> None:
        self._modules[name] = AnalyzerModule(name=name, analyze=analyze, enabled_by_default=enabled_by_default)

    def get(self, name: str) -> Optional[AnalyzerModule]:
        return self._modules.get(name)

    def list(self) -> List[str]:
        return sorted(self._modules.keys())

    def defaults(self) -> List[str]:
        return [k for k, m in self._modules.items() if m.enabled_by_default]

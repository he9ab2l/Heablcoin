############################################################
# 📘 文件说明：状态管理器
# 本文件实现的功能：市场分析状态的管理
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
# - 类: StateManager
# - 函数: get_state, set, get
#
# 🔗 主要依赖：__future__, dataclasses, market_analysis, typing
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from market_analysis.cache_manager import CacheManager


@dataclass
class StateManager:
    config: Dict[str, Any] = field(default_factory=dict)
    cache: CacheManager = field(default_factory=lambda: CacheManager(maxsize=2048))
    container: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        self.container[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.container.get(key, default)


_STATE: Optional[StateManager] = None


def get_state() -> StateManager:
    global _STATE
    if _STATE is None:
        _STATE = StateManager()
    return _STATE

############################################################
# 📘 文件说明：
# 本文件实现的功能：市场研究/分析模块：提供数据分析、质量评估与研究辅助能力。
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
# - 依赖（标准库）：__future__, dataclasses, typing
# - 依赖（第三方）：无
# - 依赖（本地）：.cache_manager
#
# 🕒 创建时间：2025-12-19
############################################################

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .cache_manager import CacheManager


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

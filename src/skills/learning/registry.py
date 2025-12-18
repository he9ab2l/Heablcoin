############################################################
# 📘 文件说明：学习注册表
# 本文件实现的功能：学习模块的配置和功能注册
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
# 数据流向：输入源 → 数据处理 → 核心算法 → 输出目标
#
# 🧩 文件结构：
# - 类: LearningModule, LearningRegistry
# - 函数: register, get, list, defaults, catalog
#
# 🔗 主要依赖：__future__, dataclasses, typing
#
# 🕒 创建时间：2025-12-18
############################################################

"""学习模块注册器"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


LearningFn = Callable[..., Dict[str, Any]]


@dataclass
class LearningModule:
    name: str
    title: str
    description: str
    handler: LearningFn
    enabled_by_default: bool = True


class LearningRegistry:
    """学习模块注册器"""

    def __init__(self) -> None:
        self._modules: Dict[str, LearningModule] = {}

    def register(
        self,
        name: str,
        title: str,
        description: str,
        handler: LearningFn,
        enabled_by_default: bool = True,
    ) -> None:
        self._modules[name] = LearningModule(
            name=name,
            title=title,
            description=description,
            handler=handler,
            enabled_by_default=enabled_by_default,
        )

    def get(self, name: str) -> Optional[LearningModule]:
        return self._modules.get(name)

    def list(self) -> List[str]:
        return sorted(self._modules.keys())

    def defaults(self) -> List[str]:
        return [k for k, m in self._modules.items() if m.enabled_by_default]

    def catalog(self) -> List[Dict[str, Any]]:
        """返回所有模块的目录"""
        return [
            {
                "key": m.name,
                "title": m.title,
                "description": m.description,
                "enabled_by_default": m.enabled_by_default,
            }
            for m in self._modules.values()
        ]


__all__ = ["LearningRegistry", "LearningModule"]

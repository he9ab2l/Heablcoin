############################################################
# 📘 文件说明：
# 本文件实现的功能：学习模块注册器
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
# - 依赖（本地）：无
#
# 🕒 创建时间：2025-12-19
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

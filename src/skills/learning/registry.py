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

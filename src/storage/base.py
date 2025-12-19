"""
存储适配层基类
==============
定义统一的存储接口，所有存储后端都需要实现这个接口。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class StorageType(str, Enum):
    """存储类型"""
    FILE = "file"
    NOTION = "notion"
    EMAIL = "email"
    DATABASE = "database"


@dataclass
class StorageResult:
    """存储操作结果"""
    success: bool
    storage_type: StorageType
    location: str  # 存储位置（文件路径、URL、ID等）
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    message: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StorageTarget(ABC):
    """存储目标抽象基类"""
    
    @property
    @abstractmethod
    def storage_type(self) -> StorageType:
        """返回存储类型"""
        pass
    
    @abstractmethod
    def save_report(self, title: str, content: str, **kwargs) -> StorageResult:
        """
        保存报告
        
        Args:
            title: 报告标题
            content: 报告内容（Markdown 或 HTML）
            **kwargs: 额外参数
        
        Returns:
            StorageResult: 存储结果
        """
        pass
    
    @abstractmethod
    def save_trade_log(self, data: Dict[str, Any], **kwargs) -> StorageResult:
        """
        保存交易日志
        
        Args:
            data: 交易数据
            **kwargs: 额外参数
        
        Returns:
            StorageResult: 存储结果
        """
        pass
    
    @abstractmethod
    def save_analysis(self, symbol: str, analysis: Dict[str, Any], **kwargs) -> StorageResult:
        """
        保存分析结果
        
        Args:
            symbol: 交易对符号
            analysis: 分析数据
            **kwargs: 额外参数
        
        Returns:
            StorageResult: 存储结果
        """
        pass
    
    def save(self, content_type: str, content: Any, **kwargs) -> StorageResult:
        """
        通用保存方法
        
        Args:
            content_type: 内容类型 (report, trade_log, analysis)
            content: 内容数据
            **kwargs: 额外参数
        
        Returns:
            StorageResult: 存储结果
        """
        if content_type == "report":
            title = kwargs.pop("title", "Untitled Report")
            return self.save_report(title, content, **kwargs)
        elif content_type == "trade_log":
            return self.save_trade_log(content, **kwargs)
        elif content_type == "analysis":
            symbol = kwargs.pop("symbol", "UNKNOWN")
            return self.save_analysis(symbol, content, **kwargs)
        else:
            return StorageResult(
                success=False,
                storage_type=self.storage_type,
                location="",
                error=f"Unknown content type: {content_type}"
            )
    
    def is_available(self) -> bool:
        """检查存储是否可用"""
        return True


class StorageManager:
    """存储管理器 - 管理多个存储后端"""
    
    def __init__(self):
        self._targets: Dict[str, StorageTarget] = {}
        self._default_target: Optional[str] = None
    
    def register(self, name: str, target: StorageTarget, default: bool = False) -> None:
        """注册存储目标"""
        self._targets[name] = target
        if default or self._default_target is None:
            self._default_target = name
    
    def get(self, name: str) -> Optional[StorageTarget]:
        """获取存储目标"""
        return self._targets.get(name)
    
    def get_default(self) -> Optional[StorageTarget]:
        """获取默认存储目标"""
        if self._default_target:
            return self._targets.get(self._default_target)
        return None
    
    def list_targets(self) -> List[str]:
        """列出所有存储目标"""
        return list(self._targets.keys())
    
    def save_to_all(self, content_type: str, content: Any, **kwargs) -> List[StorageResult]:
        """保存到所有存储目标"""
        results = []
        for name, target in self._targets.items():
            try:
                result = target.save(content_type, content, **kwargs)
                results.append(result)
            except Exception as e:
                results.append(StorageResult(
                    success=False,
                    storage_type=target.storage_type,
                    location="",
                    error=str(e)
                ))
        return results
    
    def save_to(self, target_name: str, content_type: str, content: Any, **kwargs) -> StorageResult:
        """保存到指定存储目标"""
        target = self.get(target_name)
        if not target:
            return StorageResult(
                success=False,
                storage_type=StorageType.FILE,
                location="",
                error=f"Storage target not found: {target_name}"
            )
        return target.save(content_type, content, **kwargs)


# 全局存储管理器
_storage_manager: Optional[StorageManager] = None


def get_storage_manager() -> StorageManager:
    """获取全局存储管理器"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager()
    return _storage_manager

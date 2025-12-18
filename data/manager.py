############################################################
# 📘 文件说明：数据管理器
# 本文件实现的功能：统一的数据获取、缓存和持久化管理
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
# - 类: DataManager
# - 函数: get_data_manager, get_path, save_json, load_json, save_text
#
# 🔗 主要依赖：__future__, datetime, json, os, pathlib, typing, utils
#
# 🕒 创建时间：2025-12-18
############################################################

"""
数据管理器
==========
统一管理数据文件的读写、缓存和持久化。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.smart_logger import get_logger

logger = get_logger("data_manager")


class DataManager:
    """数据管理器 - 统一管理所有数据文件"""
    
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        self.subdirs = {
            "cloud": self.base_dir / "cloud",
            "trades": self.base_dir / "trades",
            "analysis": self.base_dir / "analysis",
            "cache": self.base_dir / "cache",
            "logs": self.base_dir / "logs",
        }
        
        for subdir in self.subdirs.values():
            subdir.mkdir(parents=True, exist_ok=True)
    
    def get_path(self, category: str, filename: str) -> Path:
        """
        获取数据文件路径
        
        Args:
            category: 数据类别 (cloud, trades, analysis, cache, logs)
            filename: 文件名
        
        Returns:
            Path: 完整文件路径
        """
        if category in self.subdirs:
            return self.subdirs[category] / filename
        return self.base_dir / filename
    
    def save_json(self, category: str, filename: str, data: Any) -> bool:
        """
        保存 JSON 数据
        
        Args:
            category: 数据类别
            filename: 文件名
            data: 数据对象
        
        Returns:
            bool: 是否成功
        """
        try:
            filepath = self.get_path(category, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved JSON to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON to {category}/{filename}: {e}")
            return False
    
    def load_json(self, category: str, filename: str, default: Any = None) -> Any:
        """
        加载 JSON 数据
        
        Args:
            category: 数据类别
            filename: 文件名
            default: 默认值（文件不存在时返回）
        
        Returns:
            Any: 数据对象
        """
        try:
            filepath = self.get_path(category, filename)
            if not filepath.exists():
                return default
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Loaded JSON from {filepath}")
            return data
        except Exception as e:
            logger.error(f"Failed to load JSON from {category}/{filename}: {e}")
            return default
    
    def save_text(self, category: str, filename: str, content: str) -> bool:
        """
        保存文本数据
        
        Args:
            category: 数据类别
            filename: 文件名
            content: 文本内容
        
        Returns:
            bool: 是否成功
        """
        try:
            filepath = self.get_path(category, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.debug(f"Saved text to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save text to {category}/{filename}: {e}")
            return False
    
    def load_text(self, category: str, filename: str, default: str = "") -> str:
        """
        加载文本数据
        
        Args:
            category: 数据类别
            filename: 文件名
            default: 默认值
        
        Returns:
            str: 文本内容
        """
        try:
            filepath = self.get_path(category, filename)
            if not filepath.exists():
                return default
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"Loaded text from {filepath}")
            return content
        except Exception as e:
            logger.error(f"Failed to load text from {category}/{filename}: {e}")
            return default
    
    def list_files(self, category: str, pattern: str = "*") -> List[Path]:
        """
        列出指定类别的文件
        
        Args:
            category: 数据类别
            pattern: 文件名模式
        
        Returns:
            List[Path]: 文件路径列表
        """
        try:
            if category in self.subdirs:
                directory = self.subdirs[category]
            else:
                directory = self.base_dir
            
            return list(directory.glob(pattern))
        except Exception as e:
            logger.error(f"Failed to list files in {category}: {e}")
            return []
    
    def delete_file(self, category: str, filename: str) -> bool:
        """
        删除文件
        
        Args:
            category: 数据类别
            filename: 文件名
        
        Returns:
            bool: 是否成功
        """
        try:
            filepath = self.get_path(category, filename)
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted file {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete {category}/{filename}: {e}")
            return False
    
    def cleanup_old_files(self, category: str, days: int = 30) -> int:
        """
        清理旧文件
        
        Args:
            category: 数据类别
            days: 保留天数
        
        Returns:
            int: 删除的文件数
        """
        try:
            files = self.list_files(category)
            now = datetime.now().timestamp()
            deleted = 0
            
            for filepath in files:
                if filepath.is_file():
                    age_days = (now - filepath.stat().st_mtime) / 86400
                    if age_days > days:
                        filepath.unlink()
                        deleted += 1
            
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old files from {category}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to cleanup {category}: {e}")
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            Dict: 统计信息
        """
        stats = {
            "base_dir": str(self.base_dir),
            "categories": {}
        }
        
        for category, directory in self.subdirs.items():
            if directory.exists():
                files = list(directory.glob("*"))
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                stats["categories"][category] = {
                    "file_count": len([f for f in files if f.is_file()]),
                    "total_size_mb": f"{total_size / 1024 / 1024:.2f}",
                    "path": str(directory)
                }
        
        return stats


# 全局实例
_data_manager: Optional[DataManager] = None


def get_data_manager() -> DataManager:
    """获取全局数据管理器实例"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager

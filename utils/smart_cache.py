############################################################
# 📘 文件说明：智能缓存
# 本文件实现的功能：TTL缓存和装饰器
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
# - 类: SmartCache
# - 函数: get_smart_cache, cached, get, set, clear
#
# 🔗 主要依赖：collections, functools, time, typing
#
# 🕒 创建时间：2025-12-18
############################################################

"""
智能缓存系统 - P1-1
- L1: 内存缓存（LRU）
- TTL支持
- 缓存统计
"""

import time
import functools
from typing import Any, Callable, Dict, Optional
from collections import defaultdict


class SmartCache:
    """
    智能缓存管理器
    - 内存缓存（带TTL）
    - LRU 淘汰策略
    - 缓存命中率统计
    - 自动过期清理
    - 大小限制
    """
    
    def __init__(self, max_size: int = 1000, max_memory_mb: float = 100.0):
        self.cache: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {}
        self.access_times: Dict[str, float] = {}  # LRU tracking
        self.hit_count: Dict[str, int] = defaultdict(int)
        self.miss_count: Dict[str, int] = defaultdict(int)
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.eviction_count = 0
    
    def get(self, key: str, ttl: int = 300) -> Optional[Any]:
        """
        获取缓存（带TTL检查）
        Args:
            key: 缓存键
            ttl: 过期时间（秒）
        Returns:
            缓存值或None
        """
        if key not in self.cache:
            self.miss_count[key] += 1
            return None
        
        # 检查是否过期
        if time.time() - self.timestamps[key] > ttl:
            self._evict_key(key)
            self.miss_count[key] += 1
            return None
        
        # 更新访问时间（LRU）
        self.access_times[key] = time.time()
        self.hit_count[key] += 1
        return self.cache[key]
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        # 检查是否需要淘汰
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        # 检查内存限制
        if self._get_memory_usage() >= self.max_memory_bytes:
            self._evict_lru(count=max(1, int(self.max_size * 0.1)))  # 淘汰10%
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
        self.access_times[key] = time.time()
    
    def clear(self, pattern: str = None):
        """清除缓存"""
        if pattern is None:
            self.cache.clear()
            self.timestamps.clear()
            self.access_times.clear()
        else:
            # 清除匹配pattern的缓存
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for k in keys_to_delete:
                self._evict_key(k)
    
    def _evict_key(self, key: str) -> None:
        """淘汰单个键"""
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]
        if key in self.access_times:
            del self.access_times[key]
        self.eviction_count += 1
    
    def _evict_lru(self, count: int = 1) -> None:
        """淘汰最少使用的缓存"""
        if not self.access_times:
            return
        
        # 按访问时间排序，淘汰最旧的
        sorted_keys = sorted(self.access_times.items(), key=lambda x: x[1])
        for key, _ in sorted_keys[:count]:
            self._evict_key(key)
    
    def _get_memory_usage(self) -> int:
        """估算内存使用（字节）"""
        return sum(len(str(v).encode('utf-8')) for v in self.cache.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_hits = sum(self.hit_count.values())
        total_misses = sum(self.miss_count.values())
        total_requests = total_hits + total_misses
        hit_rate = total_hits / total_requests if total_requests > 0 else 0
        
        memory_usage = self._get_memory_usage()
        
        # 获取TOP命中的缓存键
        top_hits = sorted(
            self.hit_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "hit_rate": f"{hit_rate:.1%}",
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_keys": len(self.cache),
            "max_keys": self.max_size,
            "memory_usage_mb": f"{memory_usage / 1024 / 1024:.2f}",
            "max_memory_mb": f"{self.max_memory_bytes / 1024 / 1024:.2f}",
            "eviction_count": self.eviction_count,
            "top_hits": [
                {"key": k[:50], "hits": v} for k, v in top_hits
            ]
        }


# 全局实例
_smart_cache_instance = None


def get_smart_cache(max_size: int = 1000, max_memory_mb: float = 100.0) -> SmartCache:
    """获取全局SmartCache实例"""
    global _smart_cache_instance
    if _smart_cache_instance is None:
        _smart_cache_instance = SmartCache(max_size=max_size, max_memory_mb=max_memory_mb)
    return _smart_cache_instance


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    缓存装饰器
    Args:
        ttl: 缓存过期时间（秒），默认5分钟
        key_prefix: 缓存键前缀
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存key
            cache_key = f"{key_prefix}{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cache = get_smart_cache()
            cached_result = cache.get(cache_key, ttl=ttl)
            
            if cached_result is not None:
                return cached_result
            
            # 缓存未命中，执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator

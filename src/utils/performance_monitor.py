############################################################
# 📘 文件说明：
# 本文件实现的功能：性能监控工具
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
# - 依赖（标准库）：__future__, collections, dataclasses, functools, time, tracemalloc, typing
# - 依赖（第三方）：无
# - 依赖（本地）：utils.smart_logger
#
# 🕒 创建时间：2025-12-19
############################################################

"""
性能监控工具
支持：函数性能追踪、内存监控、瓶颈分析
"""

from __future__ import annotations

import time
import functools
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import tracemalloc

from utils.smart_logger import get_logger

logger = get_logger("system")


@dataclass
class PerformanceMetrics:
    """性能指标"""
    function_name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_call_time: float = 0.0
    error_count: int = 0
    
    def update(self, duration: float, is_error: bool = False) -> None:
        """更新指标"""
        self.call_count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.avg_time = self.total_time / self.call_count
        self.last_call_time = duration
        if is_error:
            self.error_count += 1


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.slow_threshold: float = 3.0
        self.memory_tracking: bool = False
    
    def track(self, func_name: str, duration: float, is_error: bool = False) -> None:
        """追踪函数调用"""
        if func_name not in self.metrics:
            self.metrics[func_name] = PerformanceMetrics(function_name=func_name)
        
        self.metrics[func_name].update(duration, is_error)
        
        # 慢查询警告
        if duration > self.slow_threshold:
            logger.warning(f"[PerfMonitor] Slow function: {func_name} took {duration:.2f}s (threshold: {self.slow_threshold}s)")
    
    def get_metrics(self, func_name: Optional[str] = None) -> Dict[str, Any]:
        """获取性能指标"""
        if func_name:
            metric = self.metrics.get(func_name)
            if metric:
                return {
                    "function": metric.function_name,
                    "call_count": metric.call_count,
                    "total_time": f"{metric.total_time:.2f}s",
                    "avg_time": f"{metric.avg_time:.3f}s",
                    "min_time": f"{metric.min_time:.3f}s",
                    "max_time": f"{metric.max_time:.3f}s",
                    "error_count": metric.error_count,
                    "error_rate": f"{metric.error_count / metric.call_count * 100:.1f}%" if metric.call_count > 0 else "0%"
                }
            return {}
        
        # 返回所有指标
        return {
            name: {
                "call_count": m.call_count,
                "avg_time": f"{m.avg_time:.3f}s",
                "total_time": f"{m.total_time:.2f}s",
                "error_rate": f"{m.error_count / m.call_count * 100:.1f}%" if m.call_count > 0 else "0%"
            }
            for name, m in sorted(self.metrics.items(), key=lambda x: x[1].total_time, reverse=True)
        }
    
    def get_top_slow_functions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最慢的函数"""
        sorted_metrics = sorted(
            self.metrics.values(),
            key=lambda x: x.avg_time,
            reverse=True
        )[:limit]
        
        return [
            {
                "function": m.function_name,
                "avg_time": f"{m.avg_time:.3f}s",
                "call_count": m.call_count,
                "total_time": f"{m.total_time:.2f}s"
            }
            for m in sorted_metrics
        ]
    
    def get_top_frequent_functions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取调用最频繁的函数"""
        sorted_metrics = sorted(
            self.metrics.values(),
            key=lambda x: x.call_count,
            reverse=True
        )[:limit]
        
        return [
            {
                "function": m.function_name,
                "call_count": m.call_count,
                "avg_time": f"{m.avg_time:.3f}s",
                "total_time": f"{m.total_time:.2f}s"
            }
            for m in sorted_metrics
        ]
    
    def reset(self, func_name: Optional[str] = None) -> None:
        """重置指标"""
        if func_name:
            if func_name in self.metrics:
                del self.metrics[func_name]
        else:
            self.metrics.clear()
        logger.info(f"[PerfMonitor] Metrics reset: {func_name or 'all'}")
    
    def set_slow_threshold(self, threshold: float) -> None:
        """设置慢查询阈值"""
        self.slow_threshold = threshold
        logger.info(f"[PerfMonitor] Slow threshold set to {threshold}s")


# 全局实例
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    return _performance_monitor


def monitor_performance(func: Optional[Callable] = None, *, name: Optional[str] = None):
    """
    性能监控装饰器
    
    Usage:
        @monitor_performance
        def my_function():
            pass
        
        @monitor_performance(name="custom_name")
        def another_function():
            pass
    """
    def decorator(f: Callable) -> Callable:
        func_name = name or f"{f.__module__}.{f.__name__}"
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start = time.time()
            is_error = False
            
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                is_error = True
                raise
            finally:
                duration = time.time() - start
                _performance_monitor.track(func_name, duration, is_error)
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


class MemoryProfiler:
    """内存分析器"""
    
    def __init__(self):
        self.snapshots: List[Any] = []
        self.tracking = False
    
    def start(self) -> None:
        """开始内存追踪"""
        if not self.tracking:
            tracemalloc.start()
            self.tracking = True
            logger.info("[MemoryProfiler] Started tracking")
    
    def stop(self) -> None:
        """停止内存追踪"""
        if self.tracking:
            tracemalloc.stop()
            self.tracking = False
            logger.info("[MemoryProfiler] Stopped tracking")
    
    def snapshot(self) -> None:
        """创建内存快照"""
        if self.tracking:
            snapshot = tracemalloc.take_snapshot()
            self.snapshots.append(snapshot)
            logger.info(f"[MemoryProfiler] Snapshot taken (total: {len(self.snapshots)})")
    
    def get_top_allocations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取内存分配最多的位置"""
        if not self.snapshots:
            return []
        
        snapshot = self.snapshots[-1]
        top_stats = snapshot.statistics('lineno')[:limit]
        
        return [
            {
                "file": str(stat.traceback),
                "size": f"{stat.size / 1024:.1f} KB",
                "count": stat.count
            }
            for stat in top_stats
        ]
    
    def compare_snapshots(self, index1: int = -2, index2: int = -1) -> List[Dict[str, Any]]:
        """比较两个快照的差异"""
        if len(self.snapshots) < 2:
            return []
        
        snapshot1 = self.snapshots[index1]
        snapshot2 = self.snapshots[index2]
        
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')[:10]
        
        return [
            {
                "file": str(stat.traceback),
                "size_diff": f"{stat.size_diff / 1024:.1f} KB",
                "count_diff": stat.count_diff
            }
            for stat in top_stats
        ]


# 全局内存分析器实例
_memory_profiler = MemoryProfiler()


def get_memory_profiler() -> MemoryProfiler:
    """获取全局内存分析器实例"""
    return _memory_profiler

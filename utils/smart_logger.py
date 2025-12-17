"""
智能日志系统 - P0-3
- 多通道日志（system/trading/analysis/error/performance）
- 自动轮转
- 性能监控
"""

import logging
import os
import time
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Dict, Any
from collections import defaultdict


class SmartLogger:
    """
    智能日志系统
    - 自动分类到不同通道
    - 自动轮转（按大小或时间）
    - 性能感知
    """
    
    def __init__(
        self,
        base_dir: str = "logs",
        slow_threshold_seconds: float = 3.0,
        degradation_factor: float = 2.0,
        degradation_min_calls: int = 10,
    ):
        self.base_dir = base_dir
        self.slow_threshold_seconds = float(slow_threshold_seconds)
        self.degradation_factor = float(degradation_factor)
        self.degradation_min_calls = int(degradation_min_calls)
        Path(base_dir).mkdir(parents=True, exist_ok=True)
        
        self.loggers: Dict[str, logging.Logger] = {}
        self.performance_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_calls': 0,
            'total_time': 0.0,
            'max_time': 0.0,
            'errors': 0
        })
        
        self._setup_loggers()
    
    def _setup_loggers(self):
        """配置多通道日志"""
        
        # 统一格式化器
        detailed_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s [%(name)s:%(funcName)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 1. 系统日志（按天轮转）
        system_logger = logging.getLogger('heablcoin.system')
        system_logger.setLevel(logging.INFO)
        system_logger.propagate = False
        
        system_handler = TimedRotatingFileHandler(
            os.path.join(self.base_dir, 'system.log'),
            when='midnight',
            backupCount=30,
            encoding='utf-8'
        )
        system_handler.setFormatter(detailed_formatter)
        system_logger.addHandler(system_handler)
        self.loggers['system'] = system_logger
        
        # 2. 交易日志（按大小轮转，最重要）
        trading_logger = logging.getLogger('heablcoin.trading')
        trading_logger.setLevel(logging.INFO)
        trading_logger.propagate = False
        
        trading_handler = RotatingFileHandler(
            os.path.join(self.base_dir, 'trading.log'),
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        trading_handler.setFormatter(detailed_formatter)
        trading_logger.addHandler(trading_handler)
        self.loggers['trading'] = trading_logger
        
        # 3. 分析日志（市场分析、技术指标计算）
        analysis_logger = logging.getLogger('heablcoin.analysis')
        analysis_logger.setLevel(logging.INFO)
        analysis_logger.propagate = False
        
        analysis_handler = RotatingFileHandler(
            os.path.join(self.base_dir, 'analysis.log'),
            maxBytes=20*1024*1024,  # 20MB
            backupCount=5,
            encoding='utf-8'
        )
        analysis_handler.setFormatter(simple_formatter)
        analysis_logger.addHandler(analysis_handler)
        self.loggers['analysis'] = analysis_logger
        
        # 4. 错误日志（专门收集错误）
        error_logger = logging.getLogger('heablcoin.error')
        error_logger.setLevel(logging.ERROR)
        error_logger.propagate = False
        
        error_handler = RotatingFileHandler(
            os.path.join(self.base_dir, 'error.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setFormatter(detailed_formatter)
        error_logger.addHandler(error_handler)
        self.loggers['error'] = error_logger
        
        # 5. 性能日志（新增）
        perf_logger = logging.getLogger('heablcoin.performance')
        perf_logger.setLevel(logging.INFO)
        perf_logger.propagate = False
        
        perf_handler = RotatingFileHandler(
            os.path.join(self.base_dir, 'performance.log'),
            maxBytes=20*1024*1024,  # 20MB
            backupCount=3,
            encoding='utf-8'
        )
        perf_handler.setFormatter(simple_formatter)
        perf_logger.addHandler(perf_handler)
        self.loggers['performance'] = perf_logger
        
        # 6. 学习日志（新增）
        learning_logger = logging.getLogger('heablcoin.learning')
        learning_logger.setLevel(logging.INFO)
        learning_logger.propagate = False
        
        learning_handler = RotatingFileHandler(
            os.path.join(self.base_dir, 'learning.log'),
            maxBytes=20*1024*1024,  # 20MB
            backupCount=5,
            encoding='utf-8'
        )
        learning_handler.setFormatter(simple_formatter)
        learning_logger.addHandler(learning_handler)
        self.loggers['learning'] = learning_logger
    
    def get_logger(self, channel: str = 'system') -> logging.Logger:
        """获取指定通道的logger"""
        return self.loggers.get(channel, self.loggers['system'])
    
    def log_performance(self, func_name: str, duration: float, success: bool = True):
        """记录性能指标"""
        stats = self.performance_stats[func_name]
        stats['total_calls'] += 1
        stats['total_time'] += duration
        stats['max_time'] = max(stats['max_time'], duration)
        
        if not success:
            stats['errors'] += 1
        
        # 计算平均值
        avg_time = stats['total_time'] / stats['total_calls']
        
        # 自适应采样：只记录异常情况
        perf_logger = self.get_logger('performance')
        
        # 慢查询
        if duration > self.slow_threshold_seconds:
            perf_logger.warning(
                f"🐢 SLOW: {func_name} took {duration:.2f}s (avg: {avg_time:.2f}s, max: {stats['max_time']:.2f}s)"
            )
        # 性能退化（比平均值慢2倍）
        elif stats['total_calls'] > self.degradation_min_calls and duration > avg_time * self.degradation_factor:
            perf_logger.warning(
                f"⚠️ DEGRADATION: {func_name} took {duration:.2f}s (avg: {avg_time:.2f}s)"
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return dict(self.performance_stats)


# 全局实例
_smart_logger_instance = None


def get_smart_logger(
    base_dir: str = "logs",
    slow_threshold_seconds: float = 3.0,
    degradation_factor: float = 2.0,
    degradation_min_calls: int = 10,
) -> SmartLogger:
    """获取全局SmartLogger实例"""
    global _smart_logger_instance
    if _smart_logger_instance is None:
        _smart_logger_instance = SmartLogger(
            base_dir=base_dir,
            slow_threshold_seconds=slow_threshold_seconds,
            degradation_factor=degradation_factor,
            degradation_min_calls=degradation_min_calls,
        )
    return _smart_logger_instance


def get_logger(channel: str = 'system') -> logging.Logger:
    """获取指定通道的logger快捷函数"""
    return get_smart_logger().get_logger(channel)


def log_performance(func):
    """性能记录装饰器"""
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        success = True
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise
        finally:
            duration = time.time() - start
            get_smart_logger().log_performance(func.__name__, duration, success)
    
    return wrapper

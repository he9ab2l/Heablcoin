############################################################
# 📘 文件说明：
# 本文件实现的功能：智能日志系统 - P0-3
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
# - 依赖（标准库）：collections, datetime, functools, inspect, json, logging, os, pathlib, sys, time, traceback, typing
# - 依赖（第三方）：无
# - 依赖（本地）：无
#
# 🕒 创建时间：2025-12-19
############################################################

"""
智能日志系统 - P0-3
- 多通道日志（system/trading/analysis/error/performance）
- 自动轮转
- 性能监控
"""

import logging
import os
import sys
import time
import json
import traceback
import inspect
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Dict, Any, Optional, Union
from collections import defaultdict
from functools import wraps


# 错误码前缀映射
MODULE_ERROR_CODES = {
    'system': 'E10',
    'trading': 'E20',
    'analysis': 'E30',
    'error': 'E40',
    'performance': 'E50',
    'learning': 'E60',
    'cloud': 'E70',
    'storage': 'E80',
    'mcp': 'E90',
}

# 错误计数器
_error_counters: Dict[str, int] = defaultdict(int)


def _get_beijing_time() -> str:
    """获取北京时间字符串"""
    from datetime import timezone, timedelta
    beijing_tz = timezone(timedelta(hours=8))
    return datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')


def _generate_error_code(module: str) -> str:
    """生成错误码: E + 模块编号 + 序号"""
    prefix = MODULE_ERROR_CODES.get(module, 'E99')
    _error_counters[module] += 1
    return f"{prefix}{_error_counters[module]:02d}"


class StructuredLogFormatter(logging.Formatter):
    """
    结构化日志格式化器
    输出JSON格式，包含完整的定位信息
    """
    
    def __init__(self, module_name: str = 'system'):
        super().__init__()
        self.module_name = module_name
    
    def format(self, record: logging.LogRecord) -> str:
        # 构建结构化日志
        log_entry = {
            'timestamp': _get_beijing_time(),
            'level': record.levelname,
            'module': self.module_name,
            'function': record.funcName,
            'file': record.pathname,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        
        # 如果是错误级别，添加错误码
        if record.levelno >= logging.ERROR:
            log_entry['error_code'] = _generate_error_code(self.module_name)
        
        # 添加额外上下文（如果有）
        if hasattr(record, 'context') and record.context:
            log_entry['context'] = record.context
        
        # 添加异常信息（如果有）
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': ''.join(traceback.format_exception(*record.exc_info)) if record.exc_info[0] else None
            }
        
        return json.dumps(log_entry, ensure_ascii=False)


class HumanReadableFormatter(logging.Formatter):
    """
    人类可读格式化器（带颜色和结构）
    用于控制台输出和快速调试
    """
    
    LEVEL_COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'
    
    def __init__(self, module_name: str = 'system', use_color: bool = True):
        super().__init__()
        self.module_name = module_name
        self.use_color = use_color
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = _get_beijing_time()
        level = record.levelname
        
        # 颜色处理
        if self.use_color and level in self.LEVEL_COLORS:
            level_str = f"{self.LEVEL_COLORS[level]}{level:8s}{self.RESET}"
        else:
            level_str = f"{level:8s}"
        
        # 位置信息
        location = f"{record.filename}:{record.lineno}:{record.funcName}"
        
        # 基本消息
        msg = f"[{timestamp}] {level_str} [{self.module_name}] [{location}] {record.getMessage()}"
        
        # 错误码（如果是错误级别）
        if record.levelno >= logging.ERROR:
            error_code = _generate_error_code(self.module_name)
            msg = f"[{timestamp}] {level_str} [{error_code}] [{self.module_name}] [{location}] {record.getMessage()}"
        
        return msg


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
        
        # 结构化JSON格式化器（用于机器解析和grep追踪）
        # 人类可读格式化器（用于快速调试）
        # 每个通道使用对应模块名的格式化器
        
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
        system_handler.setFormatter(StructuredLogFormatter('system'))
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
        trading_handler.setFormatter(StructuredLogFormatter('trading'))
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
        analysis_handler.setFormatter(StructuredLogFormatter('analysis'))
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
        error_handler.setFormatter(StructuredLogFormatter('error'))
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
        perf_handler.setFormatter(StructuredLogFormatter('performance'))
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
        learning_handler.setFormatter(StructuredLogFormatter('learning'))
        learning_logger.addHandler(learning_handler)
        self.loggers['learning'] = learning_logger

        # 7. 云端日志（任务/队列/worker）
        cloud_logger = logging.getLogger('heablcoin.cloud')
        cloud_logger.setLevel(logging.INFO)
        cloud_logger.propagate = False

        cloud_handler = RotatingFileHandler(
            os.path.join(self.base_dir, 'cloud.log'),
            maxBytes=20*1024*1024,  # 20MB
            backupCount=5,
            encoding='utf-8'
        )
        cloud_handler.setFormatter(StructuredLogFormatter('cloud'))
        cloud_logger.addHandler(cloud_handler)
        self.loggers['cloud'] = cloud_logger

        # 8. 存储日志（文件/Notion/Redis/Email 等适配器）
        storage_logger = logging.getLogger('heablcoin.storage')
        storage_logger.setLevel(logging.INFO)
        storage_logger.propagate = False

        storage_handler = RotatingFileHandler(
            os.path.join(self.base_dir, 'storage.log'),
            maxBytes=20*1024*1024,  # 20MB
            backupCount=5,
            encoding='utf-8'
        )
        storage_handler.setFormatter(StructuredLogFormatter('storage'))
        storage_logger.addHandler(storage_handler)
        self.loggers['storage'] = storage_logger

        # 9. MCP 调用日志（每次工具调用都写入，用于审计/回放/排障）
        mcp_logger = logging.getLogger('heablcoin.mcp')
        mcp_logger.setLevel(logging.INFO)
        mcp_logger.propagate = False

        mcp_handler = RotatingFileHandler(
            os.path.join(self.base_dir, 'mcp.log'),
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        mcp_handler.setFormatter(StructuredLogFormatter('mcp'))
        mcp_logger.addHandler(mcp_handler)
        self.loggers['mcp'] = mcp_logger
    
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
    @wraps(func)
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


def log_error_with_context(
    message: str,
    module: str = 'system',
    context: Optional[Dict[str, Any]] = None,
    exc_info: bool = False
) -> str:
    """
    记录带上下文的错误日志
    
    Args:
        message: 错误消息
        module: 模块名称
        context: 上下文信息（输入参数、运行状态等）
        exc_info: 是否包含异常堆栈
    
    Returns:
        error_code: 生成的错误码，可用于追踪
    
    Example:
        error_code = log_error_with_context(
            "Binance API 返回空响应",
            module="trading",
            context={"symbol": "BTCUSDT", "timeframe": "1m"}
        )
        # 可通过 grep E2001 快速定位
    """
    logger = get_logger(module)
    error_code = _generate_error_code(module)
    
    # 构建完整的错误记录
    frame = inspect.currentframe()
    caller_frame = frame.f_back if frame else None
    
    extra_info = {
        'error_code': error_code,
        'context': context or {},
    }
    
    if caller_frame:
        extra_info['caller_file'] = caller_frame.f_code.co_filename
        extra_info['caller_line'] = caller_frame.f_lineno
        extra_info['caller_function'] = caller_frame.f_code.co_name
    
    # 记录日志
    full_message = f"[{error_code}] {message}"
    if context:
        full_message += f" | context={json.dumps(context, ensure_ascii=False)}"
    
    logger.error(full_message, exc_info=exc_info)
    
    return error_code


class HeablcoinError(Exception):
    """
    Heablcoin 标准异常类
    带有错误码和上下文信息，禁止裸异常
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        module: str = 'system',
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or _generate_error_code(module)
        self.module = module
        self.context = context or {}
        self.timestamp = _get_beijing_time()
        
        # 获取调用位置
        frame = inspect.currentframe()
        caller_frame = frame.f_back if frame else None
        if caller_frame:
            self.file = caller_frame.f_code.co_filename
            self.line = caller_frame.f_lineno
            self.function = caller_frame.f_code.co_name
        else:
            self.file = None
            self.line = None
            self.function = None
        
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        return f"[{self.error_code}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于JSON序列化"""
        return {
            'timestamp': self.timestamp,
            'error_code': self.error_code,
            'module': self.module,
            'message': self.message,
            'file': self.file,
            'line': self.line,
            'function': self.function,
            'context': self.context,
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# 导出符号
__all__ = [
    'SmartLogger',
    'get_smart_logger',
    'get_logger',
    'log_performance',
    'log_error_with_context',
    'HeablcoinError',
    'StructuredLogFormatter',
    'HumanReadableFormatter',
    '_get_beijing_time',
    '_generate_error_code',
    'MODULE_ERROR_CODES',
]

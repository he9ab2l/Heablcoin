############################################################
# 📘 文件说明：任务执行器
# 本文件实现的功能：从任务队列取任务执行并回填结果
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
# 数据流向：MCP请求 → 任务队列 → 云端执行 → 结果回调
#
# 🧩 文件结构：
# - 类: TaskType, TaskPayload, ExecutionResult
# - 函数: get_task_executor, start_executor, stop_executor, submit_task, to_dict
#
# 🔗 主要依赖：__future__, cloud, dataclasses, datetime, enum, json, market_analysis, orchestration
#
# 🕒 创建时间：2025-12-18
############################################################

"""
云端任务执行器
==============
守护进程，从任务队列中取任务执行，并将结果回填。
根据计划书的指挥链设计，实现 MCP→云端→AI 的完整链路。
"""

from __future__ import annotations

import json
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum

from .enhanced_publisher import (
    EnhancedCloudTaskPublisher,
    EnhancedCloudTask,
    TaskStatus,
    TaskPriority,
)
from utils.smart_logger import get_logger

logger = get_logger("task_executor")


class TaskType(str, Enum):
    """标准任务类型"""
    MARKET_ANALYSIS = "market_analysis"
    PERSONAL_ANALYSIS = "personal_analysis"
    REPORT_GENERATION = "report_generation"
    AI_CALL = "ai_call"
    NOTIFICATION = "notification"
    DATA_FETCH = "data_fetch"
    STORAGE_SAVE = "storage_save"
    CUSTOM = "custom"


@dataclass
class TaskPayload:
    """标准任务 Payload 格式"""
    task_type: TaskType
    action: str  # 具体动作
    params: Dict[str, Any] = field(default_factory=dict)
    context: Optional[Dict[str, Any]] = None
    output_format: str = "json"  # json, markdown, html
    storage_target: Optional[str] = None  # file, notion, email
    notify_on_complete: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_type": self.task_type.value if isinstance(self.task_type, TaskType) else self.task_type,
            "action": self.action,
            "params": self.params,
            "context": self.context,
            "output_format": self.output_format,
            "storage_target": self.storage_target,
            "notify_on_complete": self.notify_on_complete,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskPayload":
        task_type = data.get("task_type", "custom")
        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                task_type = TaskType.CUSTOM
        
        return cls(
            task_type=task_type,
            action=data.get("action", ""),
            params=data.get("params", {}),
            context=data.get("context"),
            output_format=data.get("output_format", "json"),
            storage_target=data.get("storage_target"),
            notify_on_complete=data.get("notify_on_complete", False),
        )


@dataclass
class ExecutionResult:
    """任务执行结果"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskHandler:
    """任务处理器基类"""
    
    def can_handle(self, payload: TaskPayload) -> bool:
        """检查是否可以处理此任务"""
        return False
    
    def execute(self, payload: TaskPayload) -> ExecutionResult:
        """执行任务"""
        raise NotImplementedError


class MarketAnalysisHandler(TaskHandler):
    """市场分析任务处理器"""
    
    def can_handle(self, payload: TaskPayload) -> bool:
        return payload.task_type == TaskType.MARKET_ANALYSIS
    
    def execute(self, payload: TaskPayload) -> ExecutionResult:
        start_time = time.time()
        try:
            symbol = payload.params.get("symbol", "BTC/USDT")
            analysis_type = payload.action or "technical"
            
            # 导入市场分析模块
            from skills.market_analysis.core import MarketAnalyzer
            
            analyzer = MarketAnalyzer()
            
            if analysis_type == "technical":
                result = analyzer.analyze_technical(symbol)
            elif analysis_type == "sentiment":
                result = analyzer.analyze_sentiment(symbol)
            elif analysis_type == "full":
                result = analyzer.analyze_full(symbol)
            else:
                result = analyzer.analyze_technical(symbol)
            
            return ExecutionResult(
                success=True,
                output=result,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )


class AICallHandler(TaskHandler):
    """AI 调用任务处理器"""
    
    def can_handle(self, payload: TaskPayload) -> bool:
        return payload.task_type == TaskType.AI_CALL
    
    def execute(self, payload: TaskPayload) -> ExecutionResult:
        start_time = time.time()
        try:
            from core.orchestration.ai_roles import call_ai, AIRole
            
            role = payload.params.get("role", "ai_reasoning")
            prompt = payload.params.get("prompt", "")
            context = payload.context
            
            if not prompt:
                return ExecutionResult(
                    success=False,
                    error="Missing prompt parameter",
                    execution_time=time.time() - start_time
                )
            
            response = call_ai(
                role=role,
                prompt=prompt,
                context=context,
                max_tokens=payload.params.get("max_tokens"),
                temperature=payload.params.get("temperature"),
                forced_endpoint=payload.params.get("forced_endpoint"),
            )
            
            return ExecutionResult(
                success=response.success,
                output={
                    "content": response.content,
                    "parsed": response.parsed,
                    "endpoint": response.endpoint,
                    "role": response.role,
                },
                error=response.error,
                execution_time=time.time() - start_time,
                metadata={"latency": response.latency}
            )
            
        except Exception as e:
            logger.error(f"AI call failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )


class ReportGenerationHandler(TaskHandler):
    """报告生成任务处理器"""
    
    def can_handle(self, payload: TaskPayload) -> bool:
        return payload.task_type == TaskType.REPORT_GENERATION
    
    def execute(self, payload: TaskPayload) -> ExecutionResult:
        start_time = time.time()
        try:
            report_type = payload.action or "daily"
            
            # 根据报告类型生成
            if report_type == "daily":
                from skills.report.flexible_report.service import generate_daily_report
                result = generate_daily_report()
            elif report_type == "analysis":
                symbol = payload.params.get("symbol", "BTC/USDT")
                from skills.report.flexible_report.service import generate_analysis_report
                result = generate_analysis_report(symbol)
            else:
                result = {"error": f"Unknown report type: {report_type}"}
            
            # 如果指定了存储目标，保存报告
            if payload.storage_target and result.get("content"):
                from storage.base import get_storage_manager
                manager = get_storage_manager()
                storage_result = manager.save_to(
                    payload.storage_target,
                    "report",
                    result.get("content", ""),
                    title=result.get("title", "Report")
                )
                result["storage_result"] = {
                    "success": storage_result.success,
                    "location": storage_result.location
                }
            
            return ExecutionResult(
                success=True,
                output=result,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )


class StorageSaveHandler(TaskHandler):
    """存储保存任务处理器"""
    
    def can_handle(self, payload: TaskPayload) -> bool:
        return payload.task_type == TaskType.STORAGE_SAVE
    
    def execute(self, payload: TaskPayload) -> ExecutionResult:
        start_time = time.time()
        try:
            from storage.base import get_storage_manager
            
            manager = get_storage_manager()
            target = payload.storage_target or "file"
            content_type = payload.action or "report"
            content = payload.params.get("content", "")
            
            result = manager.save_to(
                target,
                content_type,
                content,
                **payload.params
            )
            
            return ExecutionResult(
                success=result.success,
                output={
                    "location": result.location,
                    "message": result.message
                },
                error=result.error,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Storage save failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )


class TaskExecutor:
    """任务执行器"""
    
    def __init__(self, publisher: Optional[EnhancedCloudTaskPublisher] = None):
        self.publisher = publisher or EnhancedCloudTaskPublisher()
        self.handlers: List[TaskHandler] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._poll_interval = 1.0  # 秒
        
        # 注册默认处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """注册默认任务处理器"""
        self.register_handler(MarketAnalysisHandler())
        self.register_handler(AICallHandler())
        self.register_handler(ReportGenerationHandler())
        self.register_handler(StorageSaveHandler())
    
    def register_handler(self, handler: TaskHandler) -> None:
        """注册任务处理器"""
        self.handlers.append(handler)
    
    def find_handler(self, payload: TaskPayload) -> Optional[TaskHandler]:
        """查找合适的处理器"""
        for handler in self.handlers:
            if handler.can_handle(payload):
                return handler
        return None
    
    def execute_task(self, task: EnhancedCloudTask) -> ExecutionResult:
        """执行单个任务"""
        try:
            # 解析 payload
            payload = TaskPayload.from_dict(task.payload)
            
            # 查找处理器
            handler = self.find_handler(payload)
            if not handler:
                return ExecutionResult(
                    success=False,
                    error=f"No handler found for task type: {payload.task_type}"
                )
            
            # 执行任务
            logger.info(f"Executing task {task.task_id}: {payload.task_type.value}/{payload.action}")
            result = handler.execute(payload)
            
            return result
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            return ExecutionResult(
                success=False,
                error=str(e)
            )
    
    def process_pending_tasks(self, limit: int = 10) -> int:
        """处理待执行的任务"""
        processed = 0
        
        # 获取准备好的任务
        ready_tasks = self.publisher.get_ready_tasks(limit=limit)
        
        for task in ready_tasks:
            try:
                # 更新状态为运行中
                self.publisher.update_status(task.task_id, TaskStatus.RUNNING.value)
                
                # 执行任务
                result = self.execute_task(task)
                
                # 更新任务状态
                if result.success:
                    self.publisher.update_status(
                        task.task_id,
                        TaskStatus.COMPLETED.value,
                        result={
                            "output": result.output,
                            "execution_time": result.execution_time,
                            "metadata": result.metadata
                        }
                    )
                else:
                    # 检查是否可以重试
                    if task.retry_count < task.max_retries:
                        self.publisher.retry_task(task.task_id)
                    else:
                        self.publisher.update_status(
                            task.task_id,
                            TaskStatus.FAILED.value,
                            error=result.error
                        )
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing task {task.task_id}: {e}")
                self.publisher.update_status(
                    task.task_id,
                    TaskStatus.FAILED.value,
                    error=str(e)
                )
        
        return processed
    
    def _worker_loop(self) -> None:
        """工作循环"""
        logger.info("Task executor worker started")
        
        while self._running:
            try:
                # 清理过期任务
                self.publisher.cleanup_expired()
                
                # 处理待执行任务
                processed = self.process_pending_tasks()
                
                if processed > 0:
                    logger.info(f"Processed {processed} tasks")
                
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
            
            time.sleep(self._poll_interval)
        
        logger.info("Task executor worker stopped")
    
    def start(self, poll_interval: float = 1.0) -> None:
        """启动执行器"""
        if self._running:
            return
        
        self._poll_interval = poll_interval
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
        
        logger.info("Task executor started")
    
    def stop(self) -> None:
        """停止执行器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        
        logger.info("Task executor stopped")
    
    def is_running(self) -> bool:
        """检查是否运行中"""
        return self._running


# 全局执行器实例
_executor_instance: Optional[TaskExecutor] = None


def get_task_executor() -> TaskExecutor:
    """获取全局任务执行器"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = TaskExecutor()
    return _executor_instance


def start_executor(poll_interval: float = 1.0) -> TaskExecutor:
    """启动全局任务执行器"""
    executor = get_task_executor()
    executor.start(poll_interval)
    return executor


def stop_executor() -> None:
    """停止全局任务执行器"""
    global _executor_instance
    if _executor_instance:
        _executor_instance.stop()


# 便捷函数
def submit_task(
    task_type: Union[str, TaskType],
    action: str,
    params: Optional[Dict] = None,
    priority: int = TaskPriority.NORMAL.value,
    timeout: Optional[float] = None,
    depends_on: Optional[List[str]] = None,
    storage_target: Optional[str] = None,
    notify_on_complete: bool = False,
) -> str:
    """
    提交任务到队列
    
    Args:
        task_type: 任务类型
        action: 具体动作
        params: 任务参数
        priority: 优先级
        timeout: 超时时间
        depends_on: 依赖任务 ID 列表
        storage_target: 存储目标
        notify_on_complete: 完成后是否通知
    
    Returns:
        str: 任务 ID
    """
    from .enhanced_publisher import EnhancedCloudTaskPublisher
    
    publisher = EnhancedCloudTaskPublisher()
    
    if isinstance(task_type, str):
        try:
            task_type = TaskType(task_type)
        except ValueError:
            task_type = TaskType.CUSTOM
    
    payload = TaskPayload(
        task_type=task_type,
        action=action,
        params=params or {},
        storage_target=storage_target,
        notify_on_complete=notify_on_complete,
    )
    
    task = publisher.publish(
        name=f"{task_type.value}_{action}",
        payload=payload.to_dict(),
        priority=priority,
        timeout=timeout,
        depends_on=depends_on,
        tags=[task_type.value, action]
    )
    
    return task.task_id


# 导出
__all__ = [
    "TaskType",
    "TaskPayload",
    "ExecutionResult",
    "TaskHandler",
    "TaskExecutor",
    "get_task_executor",
    "start_executor",
    "stop_executor",
    "submit_task",
]

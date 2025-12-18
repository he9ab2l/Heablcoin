############################################################
# 📘 文件说明：增强任务发布器
# 本文件实现的功能：支持优先级队列、任务依赖、批量操作、任务过期
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
# - 类: TaskPriority, TaskStatus, EnhancedCloudTask
# - 函数: is_expired, can_retry, is_ready, publish, list_tasks
#
# 🔗 主要依赖：__future__, dataclasses, enum, json, pathlib, time, typing, utils
#
# 🕒 创建时间：2025-12-18
############################################################

"""
增强的云端任务发布器
支持：优先级队列、任务依赖、批量操作、任务过期
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

import requests

from utils.smart_logger import get_logger

logger = get_logger("system")


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class EnhancedCloudTask:
    """增强的云端任务"""
    task_id: str
    name: str
    payload: Dict[str, Any]
    status: str = TaskStatus.PENDING.value
    priority: int = TaskPriority.NORMAL.value
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    schedule: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    expires_at: Optional[float] = None
    depends_on: List[str] = field(default_factory=list)
    callback_url: Optional[str] = None
    callback_attempts: int = 0
    callback_last_error: Optional[str] = None
    
    def is_expired(self) -> bool:
        """检查任务是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.retry_count < self.max_retries
    
    def is_ready(self, completed_tasks: set[str]) -> bool:
        """检查任务是否准备好执行（依赖已完成）"""
        if not self.depends_on:
            return True
        return all(dep in completed_tasks for dep in self.depends_on)


class EnhancedCloudTaskPublisher:
    """增强的云端任务发布器"""
    
    def __init__(self, path: str = "data/enhanced_cloud_tasks.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._task_handlers: Dict[str, Callable] = {}
    
    def _load(self) -> List[EnhancedCloudTask]:
        """加载任务"""
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            tasks: List[EnhancedCloudTask] = []
            for item in raw:
                tasks.append(
                    EnhancedCloudTask(
                        task_id=item.get("task_id") or "",
                        name=item.get("name") or "",
                        payload=item.get("payload") or {},
                        status=item.get("status", TaskStatus.PENDING.value),
                        priority=item.get("priority", TaskPriority.NORMAL.value),
                        created_at=item.get("created_at", time.time()),
                        updated_at=item.get("updated_at", time.time()),
                        started_at=item.get("started_at"),
                        completed_at=item.get("completed_at"),
                        schedule=item.get("schedule"),
                        tags=item.get("tags") or [],
                        result=item.get("result"),
                        error=item.get("error"),
                        retry_count=item.get("retry_count", 0),
                        max_retries=item.get("max_retries", 3),
                        timeout=item.get("timeout"),
                        expires_at=item.get("expires_at"),
                        depends_on=item.get("depends_on") or [],
                        callback_url=item.get("callback_url"),
                        callback_attempts=item.get("callback_attempts", 0),
                        callback_last_error=item.get("callback_last_error"),
                    )
                )
            return tasks
        except Exception as e:
            logger.error(f"[EnhancedPublisher] load failed: {type(e).__name__}: {e}")
            return []
    
    def _save(self, tasks: List[EnhancedCloudTask]) -> None:
        """保存任务"""
        payload = [asdict(t) for t in tasks]
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def publish(
        self,
        name: str,
        payload: Dict[str, Any],
        priority: int = TaskPriority.NORMAL.value,
        schedule: Optional[int] = None,
        tags: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        expires_in: Optional[float] = None,
        depends_on: Optional[List[str]] = None,
        max_retries: int = 3,
        callback_url: Optional[str] = None,
    ) -> EnhancedCloudTask:
        """
        发布任务
        
        Args:
            name: 任务名称
            payload: 任务负载
            priority: 优先级 (1-4)
            schedule: 定时执行间隔（秒）
            tags: 标签列表
            timeout: 超时时间（秒）
            expires_in: 过期时间（秒）
            depends_on: 依赖的任务ID列表
            max_retries: 最大重试次数
            callback_url: 回调URL
        """
        tasks = self._load()
        task_id = f"{int(time.time()*1000)}_{len(tasks)+1}"
        
        expires_at = None
        if expires_in:
            expires_at = time.time() + expires_in
        
        task = EnhancedCloudTask(
            task_id=task_id,
            name=name,
            payload=payload,
            priority=priority,
            schedule=schedule,
            tags=tags or [],
            timeout=timeout,
            expires_at=expires_at,
            depends_on=depends_on or [],
            max_retries=max_retries,
            callback_url=callback_url,
        )
        
        tasks.append(task)
        self._save(tasks)
        logger.info(f"[EnhancedPublisher] published task={name} id={task_id} priority={priority}")
        return task
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority_min: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[EnhancedCloudTask]:
        """
        列出任务
        
        Args:
            status: 状态过滤
            tags: 标签过滤（任意匹配）
            priority_min: 最小优先级
            limit: 返回数量限制
        """
        tasks = self._load()
        
        # 过滤
        if status:
            tasks = [t for t in tasks if t.status == status]
        if tags:
            tasks = [t for t in tasks if any(tag in t.tags for tag in tags)]
        if priority_min:
            tasks = [t for t in tasks if t.priority >= priority_min]
        
        # 按优先级和创建时间排序
        tasks.sort(key=lambda x: (-x.priority, x.created_at))
        
        if limit:
            tasks = tasks[:limit]
        
        return tasks
    
    def get_task(self, task_id: str) -> Optional[EnhancedCloudTask]:
        """获取单个任务"""
        tasks = self._load()
        for task in tasks:
            if task.task_id == task_id:
                return task
        return None
    
    def update_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[EnhancedCloudTask]:
        """更新任务状态"""
        tasks = self._load()
        updated = None
        
        for task in tasks:
            if task.task_id == task_id:
                task.status = status
                task.updated_at = time.time()
                
                if status == TaskStatus.RUNNING.value and task.started_at is None:
                    task.started_at = time.time()
                
                if status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]:
                    task.completed_at = time.time()
                
                if result is not None:
                    task.result = result
                
                if error is not None:
                    task.error = error
                
                updated = task
                break
        
        if updated:
            if self._should_fire_callback(updated, status):
                self._invoke_callback(updated)
            self._save(tasks)
            logger.info(f"[EnhancedPublisher] task id={task_id} -> {status}")
        
        return updated

    @staticmethod
    def _should_fire_callback(task: EnhancedCloudTask, status: str) -> bool:
        return (
            task.callback_url
            and status in {
                TaskStatus.COMPLETED.value,
                TaskStatus.FAILED.value,
                TaskStatus.CANCELLED.value,
                TaskStatus.EXPIRED.value,
            }
        )

    def _invoke_callback(self, task: EnhancedCloudTask) -> None:
        if not task.callback_url:
            return

        payload = {
            "task_id": task.task_id,
            "status": task.status,
            "result": task.result,
            "error": task.error,
            "updated_at": task.updated_at,
            "name": task.name,
            "priority": task.priority,
        }

        task.callback_attempts += 1
        try:
            resp = requests.post(task.callback_url, json=payload, timeout=10)
            if resp.status_code >= 400:
                task.callback_last_error = f"{resp.status_code}: {resp.text[:200]}"
            else:
                task.callback_last_error = None
        except Exception as exc:  # pragma: no cover
            task.callback_last_error = str(exc)
    
    def retry_task(self, task_id: str) -> Optional[EnhancedCloudTask]:
        """重试失败的任务"""
        tasks = self._load()
        
        for task in tasks:
            if task.task_id == task_id and task.status == TaskStatus.FAILED.value:
                if task.can_retry():
                    task.status = TaskStatus.PENDING.value
                    task.retry_count += 1
                    task.updated_at = time.time()
                    task.error = None
                    self._save(tasks)
                    logger.info(f"[EnhancedPublisher] task id={task_id} retry={task.retry_count}")
                    return task
                else:
                    logger.warning(f"[EnhancedPublisher] task id={task_id} max retries reached")
        
        return None
    
    def cancel_task(self, task_id: str) -> Optional[EnhancedCloudTask]:
        """取消任务"""
        return self.update_status(task_id, TaskStatus.CANCELLED.value)
    
    def cleanup_expired(self) -> int:
        """清理过期任务"""
        tasks = self._load()
        cleaned = 0
        
        for task in tasks:
            if task.is_expired() and task.status not in [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value]:
                task.status = TaskStatus.EXPIRED.value
                task.updated_at = time.time()
                cleaned += 1
        
        if cleaned > 0:
            self._save(tasks)
            logger.info(f"[EnhancedPublisher] cleaned {cleaned} expired tasks")
        
        return cleaned
    
    def get_ready_tasks(self, limit: Optional[int] = None) -> List[EnhancedCloudTask]:
        """获取准备好执行的任务（考虑依赖关系）"""
        tasks = self._load()
        
        # 获取已完成的任务ID集合
        completed_ids = {t.task_id for t in tasks if t.status == TaskStatus.COMPLETED.value}
        
        # 筛选准备好的任务
        ready = [
            t for t in tasks
            if t.status == TaskStatus.PENDING.value
            and not t.is_expired()
            and t.is_ready(completed_ids)
        ]
        
        # 按优先级排序
        ready.sort(key=lambda x: (-x.priority, x.created_at))
        
        if limit:
            ready = ready[:limit]
        
        return ready
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        tasks = self._load()
        
        stats = {
            "total": len(tasks),
            "by_status": {},
            "by_priority": {},
            "expired": 0,
            "avg_completion_time": 0.0,
        }
        
        completion_times = []
        
        for task in tasks:
            # 按状态统计
            stats["by_status"][task.status] = stats["by_status"].get(task.status, 0) + 1
            
            # 按优先级统计
            priority_name = f"priority_{task.priority}"
            stats["by_priority"][priority_name] = stats["by_priority"].get(priority_name, 0) + 1
            
            # 过期任务
            if task.is_expired():
                stats["expired"] += 1
            
            # 完成时间
            if task.completed_at and task.started_at:
                completion_times.append(task.completed_at - task.started_at)
        
        if completion_times:
            stats["avg_completion_time"] = sum(completion_times) / len(completion_times)
        
        return stats
    
    def register_handler(self, task_name: str, handler: Callable) -> None:
        """注册任务处理器"""
        self._task_handlers[task_name] = handler
        logger.info(f"[EnhancedPublisher] registered handler for task={task_name}")
    
    def execute_task(self, task: EnhancedCloudTask) -> Dict[str, Any]:
        """执行任务"""
        handler = self._task_handlers.get(task.name)
        if not handler:
            raise ValueError(f"No handler registered for task: {task.name}")
        
        self.update_status(task.task_id, TaskStatus.RUNNING.value)
        
        try:
            result = handler(task.payload)
            self.update_status(task.task_id, TaskStatus.COMPLETED.value, result=result)
            return result
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            self.update_status(task.task_id, TaskStatus.FAILED.value, error=error_msg)
            raise

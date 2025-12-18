############################################################
# 📘 文件说明：云端调度器
# 本文件实现的功能：轻量级服务端定时任务调度
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
# - 类: ScheduledTask, CloudScheduler
# - 函数: add_task, start, stop, trigger_now, snapshot
#
# 🔗 主要依赖：__future__, dataclasses, threading, time, typing, utils
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from utils.smart_logger import get_logger

logger = get_logger("system")


@dataclass
class ScheduledTask:
    name: str
    interval_seconds: int
    func: Callable[[], Any]
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    last_run: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class CloudScheduler:
    """Lightweight scheduler for server-side periodic tasks."""

    def __init__(self) -> None:
        self.tasks: Dict[str, ScheduledTask] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def add_task(self, name: str, interval_seconds: int, func: Callable[[], Any], tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        task = ScheduledTask(
            name=name,
            interval_seconds=int(interval_seconds),
            func=func,
            tags=tags or [],
            metadata=metadata or {},
        )
        with self._lock:
            self.tasks[name] = task
        logger.info(f"[CloudScheduler] registered task={name} interval={interval_seconds}s")

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="cloud-scheduler", daemon=True)
        self._thread.start()
        logger.info("[CloudScheduler] background scheduler started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("[CloudScheduler] stopped")

    def trigger_now(self, name: str) -> Optional[Any]:
        task = self.tasks.get(name)
        if not task or not task.enabled:
            return None
        logger.info(f"[CloudScheduler] manual trigger task={name}")
        try:
            return task.func()
        finally:
            task.last_run = time.time()

    def snapshot(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {
                    "name": t.name,
                    "interval_seconds": t.interval_seconds,
                    "enabled": t.enabled,
                    "last_run": t.last_run,
                    "tags": t.tags,
                    "metadata": t.metadata,
                }
                for t in self.tasks.values()
            ]

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            now = time.time()
            with self._lock:
                tasks = list(self.tasks.values())
            for task in tasks:
                if not task.enabled:
                    continue
                if task.last_run == 0 or now - task.last_run >= task.interval_seconds:
                    try:
                        task.func()
                    except Exception as e:
                        logger.error(f"[CloudScheduler] task {task.name} failed: {type(e).__name__}: {e}")
                    finally:
                        task.last_run = time.time()
            time.sleep(1.0)

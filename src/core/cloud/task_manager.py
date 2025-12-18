############################################################
# 📘 文件说明：任务管理器
# 本文件实现的功能：将MCP侧监控任务写入Redis供云端Worker读取
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
# - 函数: enqueue_monitor_task, fetch_next_task
#
# 🔗 主要依赖：__future__, os, storage, time, typing
#
# 🕒 创建时间：2025-12-18
############################################################

"""
云端任务管理
-------------
负责将 MCP 侧的监控/委托任务写入 Redis，并为云端 worker 提供读取入口。
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from storage.redis_adapter import RedisAdapter

MONITOR_QUEUE_KEY = os.getenv("REDIS_MONITOR_QUEUE_KEY", "heablcoin:monitor_queue")


def _get_redis() -> RedisAdapter:
    url = os.getenv("REDIS_URL")
    if not url:
        raise RuntimeError("未配置 REDIS_URL，无法使用云端哨兵功能")
    ssl = os.getenv("REDIS_SSL", "false").lower() == "true"
    return RedisAdapter(url=url, ssl=ssl, decode_responses=True)


def enqueue_monitor_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """写入监控任务到 Redis 列表"""
    task.setdefault("created_at", int(time.time()))
    task.setdefault("queue", MONITOR_QUEUE_KEY)
    rds = _get_redis()
    rds.push_task(MONITOR_QUEUE_KEY, task)
    return {"status": "queued", "queue": MONITOR_QUEUE_KEY, "task": task}


def fetch_next_task() -> Optional[Dict[str, Any]]:
    """从队列取出一条任务"""
    rds = _get_redis()
    return rds.pop_task(MONITOR_QUEUE_KEY)


__all__ = ["enqueue_monitor_task", "fetch_next_task", "MONITOR_QUEUE_KEY"]

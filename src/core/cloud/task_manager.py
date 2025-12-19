############################################################
# 📘 文件说明：
# 本文件实现的功能：云端任务管理
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
# - 依赖（标准库）：__future__, os, time, typing
# - 依赖（第三方）：无
# - 依赖（本地）：storage.redis_adapter
#
# 🕒 创建时间：2025-12-19
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

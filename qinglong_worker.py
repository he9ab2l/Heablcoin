############################################################
# 📘 文件说明：青龙/云端监控Worker
# 本文件实现的功能：轮询Redis监控任务，满足条件时执行通知等动作
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
# - 函数: process_task, main
#
# 🔗 主要依赖：Heablcoin, __future__, cloud, os, time, typing
#
# 🕒 创建时间：2025-12-18
############################################################

"""
青龙/云端监控 Worker
-------------------
用途：轮询 Redis 中的监控任务（由 MCP set_cloud_sentry 写入），满足条件时执行动作（当前为邮件提醒占位）。

默认 RUN_ONCE=True 只跑一轮，避免误触无限循环；在青龙上运行时设置环境变量 RUN_ONCE=false 开启持续轮询。
"""

from __future__ import annotations

import os
import time
from typing import Dict, Any

from cloud.task_manager import fetch_next_task
from Heablcoin import get_exchange, send_email  # type: ignore


def _check_condition(price: float, condition: str) -> bool:
    """极简条件解析，支持 price < X / price <= X / price > X / price >= X"""
    cond = (condition or "").replace(" ", "")
    try:
        if "<=" in cond:
            v = float(cond.split("<=")[1])
            return price <= v
        if ">=" in cond:
            v = float(cond.split(">=")[1])
            return price >= v
        if "<" in cond:
            v = float(cond.split("<")[1])
            return price < v
        if ">" in cond:
            v = float(cond.split(">")[1])
            return price > v
    except Exception:
        return False
    return False


def process_task(task: Dict[str, Any]) -> str:
    symbol = task.get("symbol") or "BTC/USDT"
    condition = task.get("condition") or ""
    action = (task.get("action") or "notify").lower()
    notes = task.get("notes") or ""

    exchange = get_exchange()
    ticker = exchange.fetch_ticker(symbol)
    last = float(ticker.get("last") or 0)

    if not _check_condition(last, condition):
        return f"skip: {symbol} price {last} not match {condition}"

    # 当前动作：发送邮件提醒
    if action in {"notify", "email_alert", "email"}:
        title = f"[Heablcoin哨兵] {symbol} 触发 {condition}"
        body = f"{symbol} 当前价格 {last}, 触发条件 {condition}。\n备注: {notes}"
        send_email(title, body, msg_type="REPORT")
        return f"notified: {symbol} {condition} @ {last}"

    return f"done: {symbol} {condition} @ {last}"


def main() -> None:
    run_once = os.getenv("RUN_ONCE", "true").lower() == "true"
    interval = int(os.getenv("WORKER_INTERVAL", "60"))
    while True:
        task = fetch_next_task()
        if task:
            msg = process_task(task)
            print(msg)
        if run_once:
            break
        time.sleep(interval)


if __name__ == "__main__":
    main()

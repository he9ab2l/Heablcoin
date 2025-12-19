############################################################
# 📘 文件说明：
# 本文件实现的功能：压力测试：模拟 200 并发任务发布并验证任务执行器可稳定处理（无数据竞争/无 JSON 写坏）。
#
# 📋 程序整体伪代码（中文）：
# 1. 初始化临时任务存储与发布器
# 2. 并发发布大量任务（200 个）
# 3. 使用 TaskExecutor + NoopHandler 顺序消费任务队列
# 4. 校验所有任务状态均为 completed 且 task_id 唯一
# 5. 清理临时目录并退出
#
# 🔄 程序流程图（逻辑流）：
# ┌──────────┐
# │ 并发提交任务 │
# └─────┬────┘
#       ↓
# ┌────────────┐
# │ 任务队列/落盘 │
# └─────┬──────┘
#       ↓
# ┌──────────┐
# │ 顺序执行校验 │
# └──────────┘
#
# 📊 数据管道说明：
# 数据流向：并发输入 → 本地临时 JSON 队列 → TaskExecutor 执行 → 状态回写 → 汇总断言
#
# 🧩 文件结构：
# - 依赖（标准库）：concurrent.futures, os, shutil, sys, tempfile, typing
# - 依赖（第三方）：无
# - 依赖（本地）：core.cloud.enhanced_publisher, core.cloud.task_executor
#
# 🕒 创建时间：2025-12-19
############################################################

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)

from core.cloud.enhanced_publisher import EnhancedCloudTaskPublisher, TaskStatus
from core.cloud.task_executor import ExecutionResult, TaskExecutor, TaskHandler, TaskPayload, TaskType


class NoopHandler(TaskHandler):
    def can_handle(self, payload: TaskPayload) -> bool:
        return payload.task_type == TaskType.CUSTOM

    def execute(self, payload: TaskPayload) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            output={"ok": True, "i": payload.params.get("i")},
            execution_time=0.0,
        )


def test_publish_200_concurrent_and_execute() -> bool:
    temp_dir = tempfile.mkdtemp()
    try:
        tasks_path = os.path.join(temp_dir, "tasks.json")
        publisher = EnhancedCloudTaskPublisher(path=tasks_path)

        def publish_one(i: int) -> str:
            task = publisher.publish(
                name="stress_noop",
                payload={"task_type": "custom", "action": "noop", "params": {"i": i}},
                priority=2,
            )
            return task.task_id

        with ThreadPoolExecutor(max_workers=32) as pool:
            task_ids = list(pool.map(publish_one, range(200)))

        assert len(task_ids) == 200
        assert len(set(task_ids)) == 200, "task_id duplicated under concurrent publish"

        executor = TaskExecutor(publisher=publisher)
        executor.handlers = [NoopHandler()]

        processed_total = 0
        for _ in range(30):
            processed = executor.process_pending_tasks(limit=100)
            processed_total += processed
            if processed == 0:
                break

        assert processed_total == 200, f"expected processed_total=200, got {processed_total}"

        tasks = publisher.list_tasks()
        assert len(tasks) == 200
        assert all(t.status == TaskStatus.COMPLETED.value for t in tasks), "not all tasks completed"
        assert all(isinstance(t.result, dict) and t.result for t in tasks), "missing task result"
        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_all_tests() -> bool:
    print("=" * 60)
    print("🔥 Stress Test: TaskExecutor (200 concurrent publishes)")
    print("=" * 60)

    ok = True
    try:
        assert test_publish_200_concurrent_and_execute()
        print("[OK] test_publish_200_concurrent_and_execute")
    except Exception as e:
        ok = False
        print(f"[FAIL] test_publish_200_concurrent_and_execute: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    print("=" * 60)
    print("PASS" if ok else "FAIL")
    print("=" * 60)
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if run_all_tests() else 1)


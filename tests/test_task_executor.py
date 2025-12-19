############################################################
# 📘 文件说明：
# 本文件实现的功能：测试用例：验证 test_task_executor 相关逻辑的正确性与回归。
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
# - 依赖（标准库）：os, sys, tempfile
# - 依赖（第三方）：无
# - 依赖（本地）：core.cloud.enhanced_publisher, core.cloud.task_executor
#
# 🕒 创建时间：2025-12-19
############################################################

import os
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, SRC_DIR)

from core.cloud.task_executor import (
    TaskExecutor,
    TaskHandler,
    TaskPayload,
    TaskType,
    ExecutionResult,
)
from core.cloud.enhanced_publisher import EnhancedCloudTaskPublisher, TaskStatus


class DummyHandler(TaskHandler):
    def can_handle(self, payload: TaskPayload) -> bool:
        return True

    def execute(self, payload: TaskPayload) -> ExecutionResult:
        return ExecutionResult(True, {"echo": payload.params})


def _publisher_path():
    tmp = tempfile.mkdtemp(prefix="task_exec_test_")
    return EnhancedCloudTaskPublisher(path=os.path.join(tmp, "tasks.json"))


def test_task_executor_flow():
    publisher = _publisher_path()
    executor = TaskExecutor(publisher=publisher)
    executor.handlers = []
    executor.register_handler(DummyHandler())

    payload = TaskPayload(
        task_type=TaskType.CUSTOM,
        action="echo",
        params={"symbol": "BTC/USDT"},
    )
    task = publisher.publish(
        name="custom_echo",
        payload=payload.to_dict(),
        priority=3,
    )

    assert executor.process_pending_tasks() == 1
    stored = publisher.get_task(task.task_id)
    assert stored.status == TaskStatus.COMPLETED.value
    assert stored.result["output"]["echo"]["symbol"] == "BTC/USDT"

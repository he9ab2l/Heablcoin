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

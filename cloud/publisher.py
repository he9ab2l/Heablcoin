from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.smart_logger import get_logger

logger = get_logger("system")


@dataclass
class CloudTask:
    task_id: str
    name: str
    payload: Dict[str, Any]
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    schedule: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None


class CloudTaskPublisher:
    """Simple file-backed task publisher for cloud/cron style jobs."""

    def __init__(self, path: str = "data/cloud_tasks.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> List[CloudTask]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            tasks: List[CloudTask] = []
            for item in raw:
                tasks.append(
                    CloudTask(
                        task_id=item.get("task_id") or "",
                        name=item.get("name") or "",
                        payload=item.get("payload") or {},
                        status=item.get("status", "pending"),
                        created_at=item.get("created_at", time.time()),
                        updated_at=item.get("updated_at", time.time()),
                        schedule=item.get("schedule"),
                        tags=item.get("tags") or [],
                        result=item.get("result"),
                    )
                )
            return tasks
        except Exception as e:
            logger.error(f"[CloudTaskPublisher] load failed: {type(e).__name__}: {e}")
            return []

    def _save(self, tasks: List[CloudTask]) -> None:
        payload = [asdict(t) for t in tasks]
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def publish(self, name: str, payload: Dict[str, Any], schedule: Optional[int] = None, tags: Optional[List[str]] = None) -> CloudTask:
        tasks = self._load()
        task_id = f"{int(time.time()*1000)}_{len(tasks)+1}"
        task = CloudTask(task_id=task_id, name=name, payload=payload, schedule=schedule, tags=tags or [])
        tasks.append(task)
        self._save(tasks)
        logger.info(f"[CloudTaskPublisher] published task={name} id={task_id}")
        return task

    def list_tasks(self, status: Optional[str] = None) -> List[CloudTask]:
        tasks = self._load()
        if status:
            return [t for t in tasks if t.status == status]
        return tasks

    def update_status(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> Optional[CloudTask]:
        tasks = self._load()
        updated = None
        for task in tasks:
            if task.task_id == task_id:
                task.status = status
                task.updated_at = time.time()
                if result is not None:
                    task.result = result
                updated = task
                break
        if updated:
            self._save(tasks)
            logger.info(f"[CloudTaskPublisher] task id={task_id} -> {status}")
        return updated

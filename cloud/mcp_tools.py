from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from cloud.publisher import CloudTaskPublisher
from cloud.enhanced_publisher import EnhancedCloudTaskPublisher, TaskPriority, TaskStatus
from cloud.scheduler import CloudScheduler
from cloud.api_manager import ApiManager, ApiEndpoint, ApiStatus
from orchestration.router import build_orchestrator_from_env, build_default_task_plan
from utils.smart_logger import get_logger

logger = get_logger("system")


def register_tools(mcp: Any) -> None:
    scheduler = CloudScheduler()
    publisher = CloudTaskPublisher()
    enhanced_publisher = EnhancedCloudTaskPublisher()
    api_manager = ApiManager()
    orchestrator = build_orchestrator_from_env()

    def _heartbeat_task() -> None:
        Path("logs/cloud_heartbeat.log").parent.mkdir(parents=True, exist_ok=True)
        Path("logs/cloud_heartbeat.log").write_text(f"{time.time()}\n", encoding="utf-8")

    def _process_pending_tasks() -> None:
        pending = publisher.list_tasks(status="pending")
        for task in pending:
            logger.info(f"[CloudScheduler] processing task id={task.task_id} name={task.name}")
            if task.name == "ai_pipeline":
                ctx = task.payload.get("context") or {}
                content = task.payload.get("content", "")
                plan = build_default_task_plan(task.payload.get("plan") or "analysis")
                result = orchestrator.run(plan=plan, user_input=content, context=ctx)
                publisher.update_status(task.task_id, status="completed", result=result)
            else:
                publisher.update_status(task.task_id, status="acknowledged", result={"note": "queued for external worker"})

    def _ensure_defaults() -> None:
        if "heartbeat" not in scheduler.tasks:
            scheduler.add_task(name="heartbeat", interval_seconds=300, func=_heartbeat_task, tags=["system"])
        if "cloud_queue" not in scheduler.tasks:
            scheduler.add_task(name="cloud_queue", interval_seconds=120, func=_process_pending_tasks, tags=["queue"])

    @mcp.tool()
    def start_cloud_scheduler() -> str:
        """启动云端定时任务调度（云心跳 + 队列消费）"""
        _ensure_defaults()
        scheduler.start()
        return json.dumps({"status": "started", "tasks": scheduler.snapshot()}, ensure_ascii=False, indent=2)

    @mcp.tool()
    def publish_cloud_task(name: str, payload: str = "{}", schedule_every_seconds: int = 0, tags: str = "") -> str:
        """发布一个云端任务，可被调度或外部工作器消费"""
        parsed_payload: Dict[str, Any] = {}
        try:
            parsed_payload = json.loads(payload) if payload else {}
        except Exception:
            parsed_payload = {"payload": payload}
        tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
        task = publisher.publish(name=name, payload=parsed_payload, schedule=schedule_every_seconds or None, tags=tag_list)
        return json.dumps({"task_id": task.task_id, "status": task.status}, ensure_ascii=False, indent=2)

    @mcp.tool()
    def list_cloud_tasks(status: str = "") -> str:
        """查看云端任务队列"""
        tasks = publisher.list_tasks(status=status or None)
        data = [task.__dict__ for task in tasks]
        return json.dumps(data, ensure_ascii=False, indent=2)

    @mcp.tool()
    def cloud_scheduler_snapshot() -> str:
        """查看云端调度任务状态"""
        return json.dumps(scheduler.snapshot(), ensure_ascii=False, indent=2)

    @mcp.tool()
    def trigger_cloud_queue() -> str:
        """手动触发一次队列消费"""
        _process_pending_tasks()
        return "队列消费完成"
    
    @mcp.tool()
    def publish_enhanced_task(
        name: str,
        payload: str = "{}",
        priority: int = 2,
        timeout: float = 0,
        expires_in: float = 0,
        depends_on: str = "",
        max_retries: int = 3,
        tags: str = ""
    ) -> str:
        """发布增强型云端任务（支持优先级、依赖、超时等）"""
        try:
            parsed_payload = json.loads(payload) if payload else {}
        except Exception:
            parsed_payload = {"payload": payload}
        
        tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
        depends_list = [d.strip() for d in (depends_on or "").split(",") if d.strip()]
        
        task = enhanced_publisher.publish(
            name=name,
            payload=parsed_payload,
            priority=priority,
            timeout=timeout if timeout > 0 else None,
            expires_in=expires_in if expires_in > 0 else None,
            depends_on=depends_list if depends_list else None,
            max_retries=max_retries,
            tags=tag_list
        )
        
        return json.dumps({
            "task_id": task.task_id,
            "status": task.status,
            "priority": task.priority,
            "expires_at": task.expires_at
        }, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    def list_enhanced_tasks(status: str = "", priority_min: int = 0, limit: int = 50) -> str:
        """查看增强型云端任务队列"""
        tasks = enhanced_publisher.list_tasks(
            status=status or None,
            priority_min=priority_min if priority_min > 0 else None,
            limit=limit
        )
        data = [{
            "task_id": t.task_id,
            "name": t.name,
            "status": t.status,
            "priority": t.priority,
            "created_at": t.created_at,
            "retry_count": t.retry_count,
            "depends_on": t.depends_on,
        } for t in tasks]
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    def get_enhanced_task_stats() -> str:
        """获取增强型任务统计信息"""
        stats = enhanced_publisher.get_stats()
        return json.dumps(stats, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    def retry_failed_task(task_id: str) -> str:
        """重试失败的任务"""
        task = enhanced_publisher.retry_task(task_id)
        if task:
            return json.dumps({"status": "retrying", "retry_count": task.retry_count}, ensure_ascii=False)
        return json.dumps({"status": "failed", "message": "Task not found or cannot retry"}, ensure_ascii=False)
    
    @mcp.tool()
    def cleanup_expired_tasks() -> str:
        """清理过期任务"""
        count = enhanced_publisher.cleanup_expired()
        return json.dumps({"cleaned": count}, ensure_ascii=False)
    
    @mcp.tool()
    def add_api_endpoint(
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        priority: int = 1,
        max_requests_per_minute: int = 60,
        timeout: float = 30.0
    ) -> str:
        """添加 API 端点到管理器"""
        endpoint = ApiEndpoint(
            name=name,
            base_url=base_url,
            api_key=api_key,
            model=model,
            priority=priority,
            max_requests_per_minute=max_requests_per_minute,
            timeout=timeout
        )
        api_manager.add_endpoint(endpoint)
        return json.dumps({"status": "added", "name": name}, ensure_ascii=False)
    
    @mcp.tool()
    def get_api_manager_stats() -> str:
        """获取 API 管理器统计信息"""
        stats = api_manager.get_stats()
        return json.dumps(stats, ensure_ascii=False, indent=2)
    
    @mcp.tool()
    def reset_api_stats() -> str:
        """重置 API 统计信息"""
        api_manager.reset_stats()
        return json.dumps({"status": "reset"}, ensure_ascii=False)

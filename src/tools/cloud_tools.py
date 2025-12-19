"""

Cloud tools: task publishing, scheduler controls, API endpoint registry.

"""


from __future__ import annotations


import json

import os

import time

from pathlib import Path

from typing import Any, Dict, Optional, List


from core.mcp_safety import mcp_tool_safe

from core.cloud.publisher import CloudTaskPublisher

from core.cloud.enhanced_publisher import EnhancedCloudTaskPublisher, TaskPriority, TaskStatus

from core.cloud.scheduler import CloudScheduler

from core.cloud.api_manager import ApiManager, ApiEndpoint, ApiStatus

from core.orchestration.router import build_orchestrator_from_env, build_default_task_plan

from core.cloud.task_executor import submit_task

from storage.redis_adapter import RedisAdapter

from utils.env_helpers import env_bool

from utils.validators import normalize_symbol, validate_price_condition

from utils.smart_logger import get_logger


logger = get_logger("system")

TASK_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "market_top_market_cap",
        "task_type": "market_analysis",
        "action": "top_market_cap",
        "title": "Top10 市值查询",
        "description": "查询当前市值最高的币种列表，并输出摘要。",
        "example_params": {"limit": 10},
    },
    {
        "id": "market_funding_rate_watch",
        "task_type": "market_analysis",
        "action": "funding_rate_watch",
        "title": "资金费率监控",
        "description": "监控指定币对资金费率并触发通知（示例参数）。",
        "example_params": {"symbol": "BTC/USDT", "threshold": 0.02},
    },
    {
        "id": "data_whale_alert",
        "task_type": "data_fetch",
        "action": "whale_alert",
        "title": "鲸鱼钱包预警",
        "description": "监控地址大额转账并推送通知（示例参数）。",
        "example_params": {"address": "0xabc...", "threshold_amount": 1000, "asset": "ETH"},
    },
    {
        "id": "report_daily_market_report",
        "task_type": "report_generation",
        "action": "daily_market_report",
        "title": "行情日报",
        "description": "生成日报类报告并可选通知。",
        "example_params": {"symbol": "BTC/USDT", "sections": ["price", "sentiment", "news"]},
    },
    {
        "id": "ai_reasoning",
        "task_type": "ai_call",
        "action": "ai_reasoning",
        "title": "AI 推理调用",
        "description": "按角色调用模型完成推理/分析类任务（示例参数）。",
        "example_params": {"role": "ai_reasoning", "prompt": "用三点概括 BTC 当前风险点"},
    },
]


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

            logger.info("[CloudScheduler] processing task=%s id=%s", task.name, task.task_id)

            if task.name == "ai_pipeline":

                ctx = task.payload.get("context") or {}

                content = task.payload.get("content", "")

                plan = build_default_task_plan(task.payload.get("plan") or "analysis")

                result = orchestrator.run(plan=plan, user_input=content, context=ctx)

                publisher.update_status(task.task_id, status="completed", result=result)

            else:

                publisher.update_status(task.task_id, status="acknowledged", result={"note": "queued"})


    def _ensure_defaults() -> None:

        if "heartbeat" not in scheduler.tasks:

            scheduler.add_task(name="heartbeat", interval_seconds=300, func=_heartbeat_task, tags=["system"])

        if "cloud_queue" not in scheduler.tasks:

            scheduler.add_task(name="cloud_queue", interval_seconds=120, func=_process_pending_tasks, tags=["queue"])


    @mcp.tool()

    @mcp_tool_safe

    def start_cloud_scheduler() -> str:

        _ensure_defaults()

        scheduler.start()

        return json.dumps({"status": "started", "tasks": scheduler.snapshot()}, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def publish_cloud_task(name: str, payload: str = "{}", schedule_every_seconds: int = 0, tags: str = "") -> str:

        try:

            parsed_payload = json.loads(payload) if payload else {}

        except Exception:

            parsed_payload = {"payload": payload}

        tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]

        task = publisher.publish(name=name, payload=parsed_payload, schedule=schedule_every_seconds or None, tags=tag_list)

        return json.dumps({"task_id": task.task_id, "status": task.status}, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def list_cloud_tasks(status: str = "") -> str:

        tasks = publisher.list_tasks(status=status or None)

        return json.dumps([task.__dict__ for task in tasks], ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def cloud_scheduler_snapshot() -> str:

        return json.dumps(scheduler.snapshot(), ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def trigger_cloud_queue() -> str:

        _process_pending_tasks()

        return "队列已刷新"


    @mcp.tool()

    @mcp_tool_safe

    def publish_enhanced_task(

        name: str,

        payload: str = "{}",

        priority: int = 2,

        timeout: float = 0,

        expires_in: float = 0,

        depends_on: str = "",

        max_retries: int = 3,

        tags: str = "",

    ) -> str:

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

            timeout=timeout or None,

            expires_in=expires_in or None,

            depends_on=depends_list or None,

            max_retries=max_retries,

            tags=tag_list,

        )

        return json.dumps(

            {"task_id": task.task_id, "status": task.status, "priority": task.priority, "expires_at": task.expires_at},

            ensure_ascii=False,

            indent=2,

        )


    @mcp.tool()

    @mcp_tool_safe

    def list_enhanced_tasks(status: str = "", priority_min: int = 0, limit: int = 50) -> str:

        tasks = enhanced_publisher.list_tasks(

            status=status or None,

            priority_min=priority_min or None,

            limit=limit,

        )

        data = []

        for t in tasks:

            data.append({

                "task_id": t.task_id,

                "name": t.name,

                "status": t.status,

                "priority": t.priority,

                "created_at": t.created_at,

                "retry_count": t.retry_count,

                "depends_on": t.depends_on,

                "callback_attempts": t.callback_attempts,

                "callback_error": t.callback_last_error,

                "tags": t.tags,

            })

        return json.dumps(data, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def get_enhanced_task_stats() -> str:

        return json.dumps(enhanced_publisher.get_stats(), ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def retry_failed_task(task_id: str) -> str:

        task = enhanced_publisher.retry_task(task_id)

        if task:

            return json.dumps({"status": "retrying", "retry_count": task.retry_count}, ensure_ascii=False)

        return json.dumps({"status": "failed", "message": "Task not found"}, ensure_ascii=False)


    @mcp.tool()

    @mcp_tool_safe

    def cleanup_expired_tasks() -> str:

        count = enhanced_publisher.cleanup_expired()

        return json.dumps({"cleaned": count}, ensure_ascii=False)


    @mcp.tool()

    @mcp_tool_safe

    def publish_task(

        task_type: str,

        action: str,

        params: str = "{}",

        priority: int = TaskPriority.NORMAL.value,

        timeout_seconds: float = 0,

        depends_on: str = "",

        notify_on_complete: bool = False,

        callback_url: str = "",

        context: str = "",

        output_format: str = "json",

        tags: str = "",

        schedule_seconds: int = 0,

        max_retries: int = 3,

        expires_in_seconds: int = 0,

    ) -> str:

        try:

            payload = json.loads(params) if params else {}

        except Exception as exc:

            return json.dumps({"success": False, "error": f"params parse error: {exc}"}, ensure_ascii=False, indent=2)

        ctx = json.loads(context) if context else None

        if "symbol" in payload:

            payload["symbol"] = normalize_symbol(str(payload["symbol"]))

        if "condition" in payload:

            try:

                validate_price_condition(str(payload["condition"]))

            except ValueError as exc:

                return json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False, indent=2)


        task_id = submit_task(

            task_type=task_type,

            action=action,

            params=payload,

            priority=priority,

            timeout=timeout_seconds or None,

            depends_on=[d.strip() for d in depends_on.split(",") if d.strip()] or None,

            storage_target=payload.get("storage_target"),

            notify_on_complete=notify_on_complete,

            context=ctx,

            output_format=output_format,

            callback_url=callback_url or None,

            tags=[t.strip() for t in tags.split(",") if t.strip()],

            schedule=schedule_seconds or None,

            max_retries=max_retries,

            expires_in=expires_in_seconds or None,

        )


        return json.dumps({"success": True, "task_id": task_id, "status": TaskStatus.PENDING.value}, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def get_task_status(task_id: str) -> str:
        task = enhanced_publisher.get_task(task_id)
        if not task:
            return json.dumps({"success": False, "error": "task not found"}, ensure_ascii=False, indent=2)
        return json.dumps({
            "success": True,

            "task": {

                "task_id": task.task_id,

                "name": task.name,

                "status": task.status,

                "priority": task.priority,

                "result": task.result,

                "error": task.error,

                "retry_count": task.retry_count,

                "callback_attempts": task.callback_attempts,

                "callback_error": task.callback_last_error,

                "tags": task.tags,

                "updated_at": task.updated_at,
            }
        }, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def list_task_templates(task_type: str = "", action: str = "") -> str:
        """
        列出任务模板（用于“AI 工单模板/一键发布”）。

        Args:
            task_type: 可选过滤（如 market_analysis / ai_call / report_generation）
            action: 可选过滤（如 top_market_cap）
        """
        ft = (task_type or "").strip().lower()
        fa = (action or "").strip().lower()

        templates = TASK_TEMPLATES
        if ft:
            templates = [t for t in templates if str(t.get("task_type", "")).lower() == ft]
        if fa:
            templates = [t for t in templates if str(t.get("action", "")).lower() == fa]

        return json.dumps({"success": True, "templates": templates}, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def render_task_template(template_id: str, overrides_json: str = "{}") -> str:
        """
        根据模板生成 publish_task 可用的参数骨架（JSON）。

        Args:
            template_id: list_task_templates 返回的模板 id
            overrides_json: JSON 字符串，合并覆盖 example_params
        """
        tid = (template_id or "").strip()
        tpl = next((t for t in TASK_TEMPLATES if t.get("id") == tid), None)
        if not tpl:
            return json.dumps({"success": False, "error": f"unknown template_id: {tid}"}, ensure_ascii=False, indent=2)

        params: Dict[str, Any] = dict(tpl.get("example_params") or {})
        if overrides_json:
            try:
                overrides = json.loads(overrides_json)
                if isinstance(overrides, dict):
                    params.update(overrides)
            except Exception:
                pass

        payload = {
            "task_type": tpl.get("task_type"),
            "action": tpl.get("action"),
            "params": params,
        }
        return json.dumps({"success": True, "template": tpl, "payload": payload}, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def wait_for_task(task_id: str, timeout_seconds: float = 60.0, poll_interval: float = 1.0) -> str:
        """
        等待增强队列任务完成（或超时），便于“发布 -> 等待 -> 取结果”的一站式体验。

        Args:
            task_id: publish_task 返回的 task_id
            timeout_seconds: 超时秒数
            poll_interval: 轮询间隔秒
        """
        start = time.time()
        timeout = max(float(timeout_seconds), 0.0)
        interval = max(float(poll_interval), 0.2)

        while True:
            task = enhanced_publisher.get_task(task_id)
            if not task:
                return json.dumps({"success": False, "error": "task not found", "task_id": task_id}, ensure_ascii=False, indent=2)

            if task.status in {
                TaskStatus.COMPLETED.value,
                TaskStatus.FAILED.value,
                TaskStatus.CANCELLED.value,
                TaskStatus.EXPIRED.value,
            }:
                return json.dumps(
                    {
                        "success": True,
                        "task_id": task_id,
                        "status": task.status,
                        "result": task.result,
                        "error": task.error,
                        "updated_at": task.updated_at,
                    },
                    ensure_ascii=False,
                    indent=2,
                )

            if timeout and (time.time() - start) >= timeout:
                return json.dumps(
                    {
                        "success": False,
                        "error": "timeout",
                        "task_id": task_id,
                        "status": task.status,
                        "updated_at": task.updated_at,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            time.sleep(interval)

    @mcp.tool()
    @mcp_tool_safe
    def add_api_endpoint(
        name: str,
        base_url: str,

        api_key: str,

        model: str,

        priority: int = 1,

        max_requests_per_minute: int = 60,

        timeout: float = 30.0,

    ) -> str:

        endpoint = ApiEndpoint(

            name=name,

            base_url=base_url,

            api_key=api_key,

            model=model,

            priority=priority,

            max_requests_per_minute=max_requests_per_minute,

            timeout=timeout,

        )

        api_manager.add_endpoint(endpoint)

        return json.dumps({"status": "added", "name": name}, ensure_ascii=False)


    @mcp.tool()

    @mcp_tool_safe

    def get_api_manager_stats() -> str:

        return json.dumps(api_manager.get_stats(), ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def reset_api_stats() -> str:

        api_manager.reset_stats()

        return json.dumps({"status": "reset"}, ensure_ascii=False)


    def _redis_from_env() -> RedisAdapter:

        url = os.getenv("REDIS_URL")

        if not url:

            host = os.getenv("REDIS_HOST")

            port = os.getenv("REDIS_PORT", "6379")

            password = os.getenv("REDIS_PASSWORD") or os.getenv("REDIS_PASS")

            if host:

                auth = f":{password}@" if password else ""

                url = f"redis://{auth}{host}:{port}/0"

        if not url:

            raise RuntimeError("REDIS_URL/REDIS_HOST 未配置，无法对接云端 Redis")

        ssl = env_bool("REDIS_SSL", False)

        return RedisAdapter(url=url, ssl=ssl, decode_responses=True)


    @mcp.tool()

    @mcp_tool_safe

    def publish_pipeline_task(

        query: str,

        task_id: str = "",

        notify: str = "",

        extra_payload_json: str = "{}",

        queue_key: str = "",

    ) -> str:

        """

        发布云端 Pipeline 任务到 Redis list（由 `src/core/cloud/pipeline_worker.py` 消费）。


        - 默认队列 key: TASK_QUEUE_KEY（默认 mcp:tasks）

        - 结果写回 hash: RESULT_HASH_KEY（默认 mcp:results）


        Args:

            query: 要搜索/总结的问题

            task_id: 可选，自定义任务 ID（留空自动生成）

            notify: 通知通道，逗号分隔（如 "serverchan,feishu"）

            extra_payload_json: 额外 payload（JSON 字符串，会合并到 payload）

            queue_key: 可选，覆盖队列 key

        """

        task_queue = (queue_key or os.getenv("TASK_QUEUE_KEY") or "mcp:tasks").strip()

        rid = _redis_from_env()


        if not task_id:

            task_id = f"task_{int(time.time() * 1000)}"


        payload: Dict[str, Any] = {"query": query}

        if notify.strip():

            payload["notify"] = [p.strip() for p in notify.split(",") if p.strip()]


        if extra_payload_json:

            try:

                extra = json.loads(extra_payload_json)

                if isinstance(extra, dict):

                    payload.update(extra)

            except Exception:

                pass


        task = {"id": task_id, "payload": payload}

        rid.push_task(task_queue, task)

        return json.dumps({"success": True, "task_id": task_id, "queue_key": task_queue}, ensure_ascii=False, indent=2)


    @mcp.tool()

    @mcp_tool_safe

    def get_pipeline_result(task_id: str, result_hash_key: str = "") -> str:
        """

        查询云端 Pipeline worker 写回的结果（Redis hash）。


        Args:

            task_id: publish_pipeline_task 返回的 task_id

            result_hash_key: 可选，覆盖结果 hash key（默认 RESULT_HASH_KEY 或 mcp:results）

        """

        key = (result_hash_key or os.getenv("RESULT_HASH_KEY") or "mcp:results").strip()

        rid = _redis_from_env()

        data = rid.hget_json(key, task_id)
        return json.dumps({"success": True, "task_id": task_id, "result_hash_key": key, "data": data}, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def wait_for_pipeline_result(
        task_id: str,
        timeout_seconds: float = 60.0,
        poll_interval: float = 1.0,
        result_hash_key: str = "",
    ) -> str:
        """
        等待云端 pipeline worker 写回结果（或超时）。

        Args:
            task_id: publish_pipeline_task 返回的 task_id
            timeout_seconds: 超时秒数
            poll_interval: 轮询间隔秒
            result_hash_key: 可选，覆盖结果 hash key（默认 RESULT_HASH_KEY 或 mcp:results）
        """
        start = time.time()
        timeout = max(float(timeout_seconds), 0.0)
        interval = max(float(poll_interval), 0.2)

        key = (result_hash_key or os.getenv("RESULT_HASH_KEY") or "mcp:results").strip()
        rid = _redis_from_env()

        while True:
            data = rid.hget_json(key, task_id)
            if data is not None:
                return json.dumps(
                    {"success": True, "task_id": task_id, "result_hash_key": key, "data": data},
                    ensure_ascii=False,
                    indent=2,
                )

            if timeout and (time.time() - start) >= timeout:
                return json.dumps(
                    {"success": False, "error": "timeout", "task_id": task_id, "result_hash_key": key},
                    ensure_ascii=False,
                    indent=2,
                )
            time.sleep(interval)

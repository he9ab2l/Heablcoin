"""
Heablcoin 云端任务 Pipeline Worker
---------------------------------
用途：消费 Redis list 任务（默认 mcp:tasks），执行 Tavily 搜索 -> DeepSeek 总结 -> 多通道通知（Server酱/飞书），写回结果到 hash（默认 mcp:results）。
环境变量（必/选）:
- REDIS_URL (必): Redis 连接串
- REDIS_SSL (选): true/false，默认 false
- TASK_QUEUE_KEY (选): 任务队列，默认 mcp:tasks
- RESULT_HASH_KEY (选): 结果 hash，默认 mcp:results
- HEABL_TAVILY_KEY (必): Tavily API Key
- HEABL_DEEPSEEK_KEY (必): DeepSeek API Key（OpenAI 兼容）
- HEABL_DEEPSEEK_MODEL (选): 默认 deepseek-chat
- SERVERCHAN_SENDKEY (选): Server酱 SendKey（用于通知）
- FEISHU_WEBHOOK (选): 飞书群机器人 Webhook
- FEISHU_SECRET (选): 飞书签名密钥
- NOTIFY_DEFAULT (选): 通知默认通道，逗号分隔，默认 serverchan
- NOTIFY_FAILOVER (选): 通道失败后的兜底通道，逗号分隔，默认 serverchan
- RUN_ONCE (选): 默认 true，设为 false 持续轮询
- WORKER_INTERVAL (选): 空轮询间隔秒，默认 5
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
import requests


# --- src 分层目录支持 ---
# 该文件可能以脚本方式运行：`python src/core/cloud/pipeline_worker.py`。
# 为确保可导入 core/tools/skills/utils/storage，在此做一次兜底 sys.path 初始化。
try:
    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    _SRC_DIR = os.path.join(_REPO_ROOT, "src")
    if _SRC_DIR not in sys.path:
        sys.path.insert(0, _SRC_DIR)
except Exception:
    pass
from storage.redis_adapter import RedisAdapter
from core.orchestration.ai_router import LLMRouter


TASK_QUEUE_KEY = os.getenv("TASK_QUEUE_KEY", "mcp:tasks")
RESULT_HASH_KEY = os.getenv("RESULT_HASH_KEY", "mcp:results")
NOTIFY_DEFAULT = [p.strip() for p in os.getenv("NOTIFY_DEFAULT", "serverchan").split(",") if p.strip()]
NOTIFY_FAILOVER = [p.strip() for p in os.getenv("NOTIFY_FAILOVER", "serverchan").split(",") if p.strip()]
RUN_ONCE = os.getenv("RUN_ONCE", "true").lower() == "true"
WORKER_INTERVAL = int(os.getenv("WORKER_INTERVAL", "5"))
LLM_PREFER = os.getenv("HEABL_LLM_DEFAULT") or os.getenv("HEABL_LLM_PREFERENCE") or os.getenv("AI_DEFAULT_PROVIDER") or ""


def _redis() -> RedisAdapter:
    url = os.getenv("REDIS_URL")
    if not url:
        host = os.getenv("REDIS_HOST")
        port = os.getenv("REDIS_PORT", "6379")
        password = os.getenv("REDIS_PASSWORD") or os.getenv("REDIS_PASS")
        if host:
            auth = f":{password}@" if password else ""
            url = f"redis://{auth}{host}:{port}/0"
    if not url:
        raise RuntimeError("REDIS_URL/REDIS_HOST 未配置，无法运行 pipeline worker")
    ssl = os.getenv("REDIS_SSL", "false").lower() == "true"
    return RedisAdapter(url=url, ssl=ssl, decode_responses=True)


def tavily_search(query: str) -> List[Dict[str, Any]]:
    api_key = os.getenv("HEABL_TAVILY_KEY") or os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("Tavily key 未配置")
    payload = {"api_key": api_key, "query": query, "max_results": 5}
    resp = requests.post("https://api.tavily.com/search", json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data.get("results") or []


def deepseek_summary(query: str, search_results: List[Dict[str, Any]]) -> str:
    content = "\n".join([f"- {item.get('title')}: {item.get('url')}" for item in search_results][:10]) or "无搜索结果"
    prompt = f"根据搜索结果回答问题，并给出简短结论。\n问题: {query}\n搜索:\n{content}"
    router = LLMRouter()
    resp = router.generate(
        prompt=prompt,
        system="You are a concise trading research assistant.",
        max_tokens=800,
        temperature=0.2,
        prefer=LLM_PREFER.strip() or None,
    )
    if not resp.get("content"):
        raise RuntimeError(f"LLM failed: {resp.get('errors')}")
    return resp["content"]


def notify_serverchan(title: str, text: str) -> Dict[str, Any]:
    key = os.getenv("SERVERCHAN_SENDKEY")
    if not key:
        return {"success": False, "error": "SERVERCHAN_SENDKEY missing"}
    url = f"https://sctapi.ftqq.com/{key}.send"
    resp = requests.post(url, data={"title": title, "desp": text}, timeout=10)
    ok = resp.status_code == 200 and resp.json().get("code") == 0
    return {"success": ok, "status_code": resp.status_code, "body": resp.text}


def _feishu_sign(secret: str, timestamp: str) -> str:
    string_to_sign = f"{timestamp}\n{secret}"
    h = hmac.new(secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(h).decode("utf-8")


def notify_feishu(title: str, text: str) -> Dict[str, Any]:
    webhook = os.getenv("FEISHU_WEBHOOK")
    if not webhook:
        return {"success": False, "error": "FEISHU_WEBHOOK missing"}
    secret = os.getenv("FEISHU_SECRET", "").strip()
    timestamp = str(int(time.time()))
    payload: Dict[str, Any] = {
        "msg_type": "text",
        "content": {"text": f"{title}\n\n{text}"},
    }
    headers = {"Content-Type": "application/json"}
    if secret:
        sign = _feishu_sign(secret, timestamp)
        payload["timestamp"] = timestamp
        payload["sign"] = sign
    resp = requests.post(webhook, headers=headers, data=json.dumps(payload), timeout=10)
    ok = resp.status_code == 200 and (resp.json().get("StatusCode") in [0, None])
    return {"success": ok, "status_code": resp.status_code, "body": resp.text}
NOTIFY_HANDLERS = {
    "serverchan": notify_serverchan,
    "feishu": notify_feishu,
}


def route_notify(channels: List[str], title: str, text: str) -> Dict[str, Any]:
    status: Dict[str, Any] = {}
    already_sent = set()
    for ch in channels:
        handler = NOTIFY_HANDLERS.get(ch)
        if not handler:
            status[ch] = {"success": False, "error": "unknown channel"}
            continue
        try:
            res = handler(title, text)
            status[ch] = res
            if res.get("success"):
                already_sent.add(ch)
        except Exception as e:
            status[ch] = {"success": False, "error": str(e)}
            if NOTIFY_FAILOVER:
                for fb in NOTIFY_FAILOVER:
                    if fb in already_sent:
                        continue
                    fb_handler = NOTIFY_HANDLERS.get(fb)
                    if not fb_handler:
                        status[fb] = {"success": False, "error": "unknown failover"}
                        continue
                    try:
                        fb_res = fb_handler(title, text)
                        status[fb] = fb_res
                        if fb_res.get("success"):
                            already_sent.add(fb)
                            break
                    except Exception as fb_e:
                        status[fb] = {"success": False, "error": str(fb_e)}
    return status


def process_task(task: Dict[str, Any]) -> Dict[str, Any]:
    task_id = task.get("id") or f"task_{int(time.time() * 1000)}"
    payload = task.get("payload") or {}
    query = payload.get("query") or task.get("query") or "No query provided"
    notify_targets = payload.get("notify") or NOTIFY_DEFAULT
    if isinstance(notify_targets, str):
        notify_targets = [p.strip() for p in notify_targets.split(",") if p.strip()]
    search_results = tavily_search(query)
    summary = deepseek_summary(query, search_results)
    title = f"[Heablcoin] {query}"
    text = summary
    notify_status = route_notify(notify_targets, title, text)
    return {
        "task_id": task_id,
        "query": query,
        "notify": notify_targets,
        "search_results": search_results,
        "summary": summary,
        "notify_status": notify_status,
        "timestamp": int(time.time()),
    }


def main() -> None:
    rds = _redis()
    while True:
        task = rds.pop_task(TASK_QUEUE_KEY)
        if not task:
            if RUN_ONCE:
                break
            time.sleep(WORKER_INTERVAL)
            continue
        if isinstance(task, str):
            try:
                task = json.loads(task)
            except Exception:
                task = {"id": f"task_{int(time.time() * 1000)}", "payload": {"query": str(task)}}
        try:
            result = process_task(task)
            rds.hset_json(RESULT_HASH_KEY, result["task_id"], result)
            print(f"[OK] {result['task_id']} {result.get('query')}")
        except Exception as e:
            fail = {
                "task_id": task.get("id"),
                "error": str(e),
                "payload": task,
                "timestamp": int(time.time()),
            }
            rds.hset_json(RESULT_HASH_KEY, fail["task_id"] or f"task_{int(time.time()*1000)}", fail)
            print(f"[FAIL] {task.get('id')} {e}")
        if RUN_ONCE:
            break
if __name__ == "__main__":
    main()

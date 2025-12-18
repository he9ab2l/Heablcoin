############################################################
# 📘 文件说明：Redis存储适配器
# 本文件实现的功能：Redis缓存和队列操作
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
# 数据流向：应用层 → 存储适配器 → 外部存储（文件/Redis/Notion/邮件）
#
# 🧩 文件结构：
# - 类: RedisAdapter
# - 函数: set_json, get_json, push_task, pop_task, hset_json
#
# 🔗 主要依赖：__future__, json, redis, typing
#
# 🕒 创建时间：2025-12-18
############################################################

"""
Redis 适配器（可选）
------------------
封装基础的列表推送/弹出与键值读写，便于云端哨兵与本地 MCP 协同。
依赖 redis-py，如果未安装则在实例化时抛出友好错误。
"""

from __future__ import annotations

import json
from typing import Any, Optional


class RedisAdapter:
    def __init__(self, url: str, ssl: bool = False, decode_responses: bool = True) -> None:
        try:
            import redis  # type: ignore
        except Exception as e:  # pragma: no cover - optional dependency
            raise RuntimeError("redis 库未安装，请先 pip install redis") from e
        ssl_params = {"ssl": True} if ssl else {}
        self._client = redis.from_url(url, decode_responses=decode_responses, **ssl_params)

    # 基础 KV
    def set_json(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        self._client.set(key, payload, ex=expire)

    def get_json(self, key: str) -> Any:
        raw = self._client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return raw

    # 队列（列表）操作
    def push_task(self, list_key: str, task: Any) -> None:
        payload = json.dumps(task, ensure_ascii=False)
        self._client.rpush(list_key, payload)

    def pop_task(self, list_key: str) -> Optional[Any]:
        raw = self._client.lpop(list_key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return raw

    # Hash 操作
    def hset_json(self, hash_key: str, field: str, value: Any) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        self._client.hset(hash_key, field, payload)

    def hget_json(self, hash_key: str, field: str) -> Any:
        raw = self._client.hget(hash_key, field)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return raw


__all__ = ["RedisAdapter"]

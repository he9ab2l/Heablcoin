############################################################
# 📘 文件说明：
# 本文件实现的功能：市场研究/分析模块：提供数据分析、质量评估与研究辅助能力。
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
# - 依赖（标准库）：__future__, collections, functools, threading, time, typing
# - 依赖（第三方）：无
# - 依赖（本地）：无
#
# 🕒 创建时间：2025-12-19
############################################################

from __future__ import annotations

from collections import OrderedDict
import functools
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple


class CacheManager:
    def __init__(self, maxsize: int = 2048) -> None:
        self._maxsize = int(maxsize) if int(maxsize) > 0 else 2048
        self._lock = threading.RLock()
        self._data: "OrderedDict[str, Tuple[float, Any]]" = OrderedDict()

    def get(self, key: str) -> Any:
        now = time.time()
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at and expires_at < now:
                try:
                    del self._data[key]
                except Exception:
                    pass
                return None
            self._data.move_to_end(key)
            return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        ttl = int(ttl_seconds)
        expires_at = time.time() + ttl if ttl > 0 else 0.0
        with self._lock:
            self._data[key] = (expires_at, value)
            self._data.move_to_end(key)
            while len(self._data) > self._maxsize:
                self._data.popitem(last=False)

    def cached(
        self,
        ttl_seconds: int,
        key_prefix: str = "",
        key_fn: Optional[Callable[..., str]] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        ttl = int(ttl_seconds)

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(fn)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if key_fn is not None:
                    k = key_fn(*args, **kwargs)
                else:
                    k = f"{fn.__module__}.{fn.__name__}:{args!r}:{kwargs!r}"
                key = f"{key_prefix}{k}"
                hit = self.get(key)
                if hit is not None:
                    return hit
                val = fn(*args, **kwargs)
                self.set(key, val, ttl)
                return val

            return wrapper

        return decorator

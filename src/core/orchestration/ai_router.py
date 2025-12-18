############################################################
# 📘 文件说明：AI路由器
# 本文件实现的功能：AI请求的路由和分发
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
# - 类: LLMRouter
# - 函数: generate, health_snapshot
#
# 🔗 主要依赖：__future__, orchestration, os, time, typing, utils
#
# 🕒 创建时间：2025-12-18
############################################################

"""
LLM Router
----------
统一管理多家 LLM 提供商，支持自动选择、失败降级、健康标记。
"""
from __future__ import annotations

import os
import time
from typing import Dict, List, Any, Optional

from .providers import build_default_providers, AiProvider, ProviderResponse, EchoProvider
from utils.smart_logger import get_logger

logger = get_logger("system")


def _parse_pref() -> List[str]:
    pref = os.getenv("HEABL_LLM_PREFERENCE") or os.getenv("HEABL_LLM_DEFAULT") or os.getenv("AI_DEFAULT_PROVIDER")
    if not pref:
        return []
    parts = [p.strip() for p in pref.split(",") if p.strip()]
    return parts


class LLMRouter:
    def __init__(self, providers: Optional[Dict[str, AiProvider]] = None) -> None:
        self.providers = providers or build_default_providers()
        self.health: Dict[str, Dict[str, Any]] = {name: {"ok": True, "last_error": None, "last_ts": 0} for name in self.providers.keys()}

    def _candidate_list(self, prefer: Optional[str] = None) -> List[str]:
        order: List[str] = []
        if prefer and prefer in self.providers:
            order.append(prefer)
        order.extend([p for p in _parse_pref() if p in self.providers and p not in order])
        # fallback: add remaining
        for name in self.providers.keys():
            if name not in order:
                order.append(name)
        return order

    def generate(self, prompt: str, system: str = "", max_tokens: int = 512, temperature: float = 0.3, prefer: Optional[str] = None) -> Dict[str, Any]:
        order = self._candidate_list(prefer)
        errors: Dict[str, Any] = {}
        for name in order:
            provider = self.providers.get(name)
            if not provider:
                continue
            try:
                start = time.time()
                resp: ProviderResponse = provider.generate(prompt=prompt, system=system, max_tokens=max_tokens, temperature=temperature)
                latency = time.time() - start
                self.health[name] = {"ok": True, "last_error": None, "last_ts": time.time()}
                return {
                    "success": True,
                    "provider": resp.provider or name,
                    "model": resp.model,
                    "latency": latency,
                    "content": resp.text,
                    "raw": resp.raw,
                    "errors": errors,
                }
            except Exception as e:
                self.health[name] = {"ok": False, "last_error": str(e), "last_ts": time.time()}
                errors[name] = str(e)
                logger.warning(f"[LLMRouter] provider {name} failed: {e}")
                continue
        # if all failed, return echo fallback
        echo = EchoProvider()
        resp = echo.generate(prompt=prompt, system=system, max_tokens=max_tokens, temperature=temperature)
        return {
            "success": False,
            "provider": resp.provider,
            "model": resp.model,
            "latency": resp.latency,
            "content": resp.text,
            "raw": resp.raw,
            "errors": errors,
        }

    def health_snapshot(self) -> Dict[str, Any]:
        return self.health


__all__ = ["LLMRouter"]

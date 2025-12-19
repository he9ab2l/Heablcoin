"""
云端 API 管理器 - 多 API 提供商支持
支持：OpenAI, DeepSeek, Anthropic, 自定义端点
功能：负载均衡、故障转移、速率限制、重试机制
"""
from __future__ import annotations
import time
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict
from enum import Enum
from utils.smart_logger import get_logger


logger = get_logger("system")


class ApiStatus(Enum):
    """API 状态枚举"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


@dataclass


class ApiEndpoint:
    """API 端点配置"""
    name: str
    base_url: str
    api_key: str
    model: str
    priority: int = 1
    max_requests_per_minute: int = 60
    timeout: float = 30.0
    status: ApiStatus = ApiStatus.ACTIVE
    last_success: float = field(default_factory=time.time)
    last_failure: float = 0.0
    failure_count: int = 0
    success_count: int = 0
    total_latency: float = 0.0
    @property
    def avg_latency(self) -> float:
        """平均延迟"""
        if self.success_count == 0:
            return 0.0
        return self.total_latency / self.success_count
    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total


@dataclass


class RateLimiter:
    """速率限制器"""
    max_requests: int
    window_seconds: float = 60.0
    requests: List[float] = field(default_factory=list)
    def can_request(self) -> bool:
        """检查是否可以发起请求"""
        now = time.time()
        self.requests = [t for t in self.requests if now - t < self.window_seconds]
        return len(self.requests) < self.max_requests
    def record_request(self) -> None:
        """记录请求"""
        self.requests.append(time.time())
    def wait_time(self) -> float:
        """需要等待的时间（秒）"""
        if self.can_request():
            return 0.0
        now = time.time()
        self.requests = [t for t in self.requests if now - t < self.window_seconds]
        if not self.requests:
            return 0.0
        oldest = min(self.requests)
        return max(0.0, self.window_seconds - (now - oldest))


class ApiManager:
    """
    多 API 管理器
    - 支持多个 API 提供商
    - 自动负载均衡
    - 故障转移
    - 速率限制
    - 重试机制
    """
    def __init__(self, endpoints: Optional[List[ApiEndpoint]] = None):
        self.endpoints: Dict[str, ApiEndpoint] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        if endpoints:
            for ep in endpoints:
                self.add_endpoint(ep)
    def add_endpoint(self, endpoint: ApiEndpoint) -> None:
        """添加 API 端点"""
        self.endpoints[endpoint.name] = endpoint
        self.rate_limiters[endpoint.name] = RateLimiter(
            max_requests=endpoint.max_requests_per_minute,
            window_seconds=60.0
        )
        logger.info(f"[ApiManager] Added endpoint: {endpoint.name} (priority={endpoint.priority})")
    def remove_endpoint(self, name: str) -> None:
        """移除 API 端点"""
        if name in self.endpoints:
            del self.endpoints[name]
            del self.rate_limiters[name]
            logger.info(f"[ApiManager] Removed endpoint: {name}")
    def get_available_endpoints(self, exclude: Optional[List[str]] = None) -> List[ApiEndpoint]:
        """获取可用的端点列表（按优先级排序）"""
        exclude = exclude or []
        available = []
        for name, ep in self.endpoints.items():
            if name in exclude:
                continue
            # 检查状态
            if ep.status == ApiStatus.FAILED:
                # 检查是否可以重试（失败后等待时间）
                if time.time() - ep.last_failure < 60.0:
                    continue
                else:
                    ep.status = ApiStatus.ACTIVE
                    ep.failure_count = 0
            # 检查速率限制
            limiter = self.rate_limiters.get(name)
            if limiter and not limiter.can_request():
                ep.status = ApiStatus.RATE_LIMITED
                continue
            available.append(ep)
        # 按优先级和成功率排序
        available.sort(key=lambda x: (-x.priority, -x.success_rate, x.avg_latency))
        return available
    def select_endpoint(self, strategy: str = "priority", exclude: Optional[List[str]] = None) -> Optional[ApiEndpoint]:
        """
        选择最佳端点
        Args:
            strategy: 选择策略 (priority, round_robin, least_latency, random)
            exclude: 排除的端点名称列表
        """
        available = self.get_available_endpoints(exclude=exclude)
        if not available:
            return None
        if strategy == "priority":
            return available[0]
        elif strategy == "random":
            return random.choice(available)
        elif strategy == "least_latency":
            return min(available, key=lambda x: x.avg_latency or float('inf'))
        elif strategy == "round_robin":
            # 简单轮询：选择最少使用的
            return min(available, key=lambda x: x.success_count + x.failure_count)
        else:
            return available[0]
    def call_with_retry(
        self,
        func: Callable[[ApiEndpoint], Any],
        max_retries: int = 3,
        strategy: str = "priority",
        backoff_factor: float = 1.5
    ) -> tuple[Any, Optional[ApiEndpoint]]:
        """
        使用重试机制调用 API
        Args:
            func: 调用函数，接收 ApiEndpoint 参数
            max_retries: 最大重试次数
            strategy: 端点选择策略
            backoff_factor: 退避因子
        Returns:
            (result, endpoint) 元组
        """
        tried_endpoints = []
        last_error = None
        for attempt in range(max_retries):
            endpoint = self.select_endpoint(strategy=strategy, exclude=tried_endpoints)
            if not endpoint:
                logger.warning(f"[ApiManager] No available endpoints (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    logger.info(f"[ApiManager] Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                continue
            tried_endpoints.append(endpoint.name)
            limiter = self.rate_limiters.get(endpoint.name)
            # 检查速率限制
            if limiter and not limiter.can_request():
                wait = limiter.wait_time()
                if wait > 0:
                    logger.info(f"[ApiManager] Rate limited on {endpoint.name}, waiting {wait:.1f}s")
                    time.sleep(min(wait, 5.0))
            # 记录请求
            if limiter:
                limiter.record_request()
            # 执行调用
            start_time = time.time()
            try:
                result = func(endpoint)
                latency = time.time() - start_time
                # 更新统计
                endpoint.success_count += 1
                endpoint.total_latency += latency
                endpoint.last_success = time.time()
                endpoint.status = ApiStatus.ACTIVE
                logger.info(f"[ApiManager] Success on {endpoint.name} (latency={latency:.2f}s)")
                return result, endpoint
            except Exception as e:
                latency = time.time() - start_time
                endpoint.failure_count += 1
                endpoint.last_failure = time.time()
                last_error = e
                # 连续失败则标记为失败状态
                if endpoint.failure_count >= 3:
                    endpoint.status = ApiStatus.FAILED
                    logger.error(f"[ApiManager] Endpoint {endpoint.name} marked as FAILED")
                logger.warning(f"[ApiManager] Failed on {endpoint.name} (attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {e}")
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    time.sleep(wait_time)
        # 所有重试都失败
        error_msg = f"All API endpoints failed after {max_retries} attempts"
        if last_error:
            error_msg += f". Last error: {type(last_error).__name__}: {last_error}"
        logger.error(f"[ApiManager] {error_msg}")
        raise RuntimeError(error_msg)
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_endpoints": len(self.endpoints),
            "endpoints": {}
        }
        for name, ep in self.endpoints.items():
            limiter = self.rate_limiters.get(name)
            stats["endpoints"][name] = {
                "status": ep.status.value,
                "priority": ep.priority,
                "success_count": ep.success_count,
                "failure_count": ep.failure_count,
                "success_rate": f"{ep.success_rate:.1%}",
                "avg_latency": f"{ep.avg_latency:.2f}s",
                "rate_limit": f"{len(limiter.requests) if limiter else 0}/{ep.max_requests_per_minute}",
            }
        return stats
    def reset_stats(self) -> None:
        """重置统计信息"""
        for ep in self.endpoints.values():
            ep.success_count = 0
            ep.failure_count = 0
            ep.total_latency = 0.0
            ep.status = ApiStatus.ACTIVE
        logger.info("[ApiManager] Stats reset")
    def record_success(self, endpoint_name: str, latency: float) -> None:
        """记录成功调用"""
        if endpoint_name in self.endpoints:
            ep = self.endpoints[endpoint_name]
            ep.success_count += 1
            ep.total_latency += latency
            ep.last_success = time.time()
            ep.status = ApiStatus.ACTIVE
    def record_failure(self, endpoint_name: str) -> None:
        """记录失败调用"""
        if endpoint_name in self.endpoints:
            ep = self.endpoints[endpoint_name]
            ep.failure_count += 1
            ep.last_failure = time.time()
            if ep.failure_count >= 3:
                ep.status = ApiStatus.FAILED
    def get_endpoint(self, name: str) -> Optional[ApiEndpoint]:
        """获取指定端点"""
        return self.endpoints.get(name)
    def is_endpoint_available(self, name: str) -> bool:
        """检查端点是否可用"""
        ep = self.endpoints.get(name)
        if not ep:
            return False
        if ep.status == ApiStatus.FAILED:
            # 检查是否可以恢复
            if time.time() - ep.last_failure > 60:
                ep.status = ApiStatus.ACTIVE
                return True
            return False
        return ep.status in [ApiStatus.ACTIVE, ApiStatus.DEGRADED]
    def get_available_endpoints(self) -> List[ApiEndpoint]:
        """获取所有可用端点"""
        available = []
        for name, ep in self.endpoints.items():
            if self.is_endpoint_available(name):
                available.append(ep)
        return sorted(available, key=lambda x: x.priority)
# 全局 API 管理器实例
_api_manager_instance: Optional[ApiManager] = None


def get_api_manager() -> ApiManager:
    """获取全局 API 管理器实例"""
    global _api_manager_instance
    if _api_manager_instance is None:
        _api_manager_instance = ApiManager()
        _init_default_endpoints(_api_manager_instance)
    return _api_manager_instance


def _init_default_endpoints(manager: ApiManager) -> None:
    """初始化默认端点（从环境变量）"""
    import os


    # OpenAI
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key:
        manager.add_endpoint(ApiEndpoint(
            name="openai",
            base_url="https://api.openai.com/v1",
            api_key=openai_key,
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            priority=1,
            max_requests_per_minute=60,
            timeout=float(os.getenv("AI_TIMEOUT", "30"))
        ))
    # DeepSeek
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    if deepseek_key:
        manager.add_endpoint(ApiEndpoint(
            name="deepseek",
            base_url="https://api.deepseek.com/v1",
            api_key=deepseek_key,
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            priority=2,
            max_requests_per_minute=100,
            timeout=float(os.getenv("AI_TIMEOUT", "30"))
        ))
    # Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        manager.add_endpoint(ApiEndpoint(
            name="anthropic",
            base_url="https://api.anthropic.com/v1",
            api_key=anthropic_key,
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
            priority=1,
            max_requests_per_minute=60,
            timeout=float(os.getenv("AI_TIMEOUT", "30"))
        ))
    # Gemini
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key:
        manager.add_endpoint(ApiEndpoint(
            name="gemini",
            base_url="https://generativelanguage.googleapis.com/v1beta",
            api_key=gemini_key,
            model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            priority=2,
            max_requests_per_minute=60,
            timeout=float(os.getenv("AI_TIMEOUT", "30"))
        ))
    # Groq (OpenAI-compatible)
    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key:
        manager.add_endpoint(ApiEndpoint(
            name="groq",
            base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            api_key=groq_key,
            model=os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
            priority=2,
            max_requests_per_minute=90,
            timeout=float(os.getenv("AI_TIMEOUT", "30"))
        ))
    # Moonshot (Kimi, OpenAI-compatible)
    moonshot_key = os.getenv("MOONSHOT_API_KEY", "")
    if moonshot_key:
        manager.add_endpoint(ApiEndpoint(
            name="moonshot",
            base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1"),
            api_key=moonshot_key,
            model=os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k"),
            priority=2,
            max_requests_per_minute=60,
            timeout=float(os.getenv("AI_TIMEOUT", "30"))
        ))
    # Zhipu (GLM, OpenAI-compatible)
    zhipu_key = os.getenv("ZHIPU_API_KEY", "")
    if zhipu_key:
        manager.add_endpoint(ApiEndpoint(
            name="zhipu",
            base_url=os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
            api_key=zhipu_key,
            model=os.getenv("ZHIPU_MODEL", "glm-4"),
            priority=2,
            max_requests_per_minute=60,
            timeout=float(os.getenv("AI_TIMEOUT", "30"))
        ))

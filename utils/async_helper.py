"""
异步辅助工具
支持：异步批量操作、并发控制、超时管理
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, List, Optional, TypeVar, Coroutine
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from utils.smart_logger import get_logger

logger = get_logger("system")

T = TypeVar('T')


@dataclass
class AsyncResult:
    """异步操作结果"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    index: int = 0


class AsyncBatchProcessor:
    """异步批量处理器"""
    
    def __init__(self, max_concurrent: int = 5, timeout: float = 30.0):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
    
    def process_batch(
        self,
        items: List[Any],
        func: Callable[[Any], Any],
        show_progress: bool = False
    ) -> List[AsyncResult]:
        """
        批量处理项目
        
        Args:
            items: 要处理的项目列表
            func: 处理函数
            show_progress: 是否显示进度
        
        Returns:
            结果列表
        """
        results: List[AsyncResult] = []
        futures = []
        
        for idx, item in enumerate(items):
            future = self.executor.submit(self._process_single, func, item, idx)
            futures.append(future)
        
        for idx, future in enumerate(futures):
            try:
                result = future.result(timeout=self.timeout)
                results.append(result)
                
                if show_progress:
                    logger.info(f"[AsyncBatch] Progress: {idx + 1}/{len(items)}")
                    
            except FutureTimeoutError:
                results.append(AsyncResult(
                    success=False,
                    error=f"Timeout after {self.timeout}s",
                    index=idx
                ))
            except Exception as e:
                results.append(AsyncResult(
                    success=False,
                    error=f"{type(e).__name__}: {e}",
                    index=idx
                ))
        
        return results
    
    def _process_single(self, func: Callable, item: Any, index: int) -> AsyncResult:
        """处理单个项目"""
        start = time.time()
        try:
            result = func(item)
            return AsyncResult(
                success=True,
                result=result,
                duration=time.time() - start,
                index=index
            )
        except Exception as e:
            return AsyncResult(
                success=False,
                error=f"{type(e).__name__}: {e}",
                duration=time.time() - start,
                index=index
            )
    
    def shutdown(self):
        """关闭执行器"""
        self.executor.shutdown(wait=True)


class RateLimitedExecutor:
    """速率限制的执行器"""
    
    def __init__(self, max_per_second: float = 10.0):
        self.max_per_second = max_per_second
        self.min_interval = 1.0 / max_per_second
        self.last_execution = 0.0
    
    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """执行函数（带速率限制）"""
        now = time.time()
        elapsed = now - self.last_execution
        
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_execution = time.time()
        return func(*args, **kwargs)
    
    def execute_batch(
        self,
        items: List[Any],
        func: Callable[[Any], Any],
        show_progress: bool = False
    ) -> List[Any]:
        """批量执行（带速率限制）"""
        results = []
        
        for idx, item in enumerate(items):
            result = self.execute(func, item)
            results.append(result)
            
            if show_progress and (idx + 1) % 10 == 0:
                logger.info(f"[RateLimited] Progress: {idx + 1}/{len(items)}")
        
        return results


class TimeoutManager:
    """超时管理器"""
    
    @staticmethod
    def with_timeout(func: Callable[..., T], timeout: float, *args, **kwargs) -> T:
        """
        执行函数并设置超时
        
        Args:
            func: 要执行的函数
            timeout: 超时时间（秒）
            *args, **kwargs: 函数参数
        
        Returns:
            函数结果
        
        Raises:
            TimeoutError: 超时异常
        """
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(func, *args, **kwargs)
        
        try:
            result = future.result(timeout=timeout)
            return result
        except FutureTimeoutError:
            future.cancel()
            raise TimeoutError(f"Function execution timeout after {timeout}s")
        finally:
            executor.shutdown(wait=False)
    
    @staticmethod
    def with_retry_and_timeout(
        func: Callable[..., T],
        max_retries: int = 3,
        timeout: float = 30.0,
        backoff_factor: float = 1.5,
        *args,
        **kwargs
    ) -> T:
        """
        执行函数并设置重试和超时
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
            backoff_factor: 退避因子
            *args, **kwargs: 函数参数
        
        Returns:
            函数结果
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return TimeoutManager.with_timeout(func, timeout, *args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"[TimeoutManager] Attempt {attempt + 1} failed, retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
        
        raise RuntimeError(f"All {max_retries} attempts failed. Last error: {last_error}")


class ConcurrencyLimiter:
    """并发限制器"""
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_count = 0
    
    async def acquire(self):
        """获取许可"""
        await self.semaphore.acquire()
        self.active_count += 1
    
    def release(self):
        """释放许可"""
        self.semaphore.release()
        self.active_count = max(0, self.active_count - 1)
    
    def get_active_count(self) -> int:
        """获取当前活跃数量"""
        return self.active_count


def run_with_concurrency_limit(
    tasks: List[Callable],
    max_concurrent: int = 5,
    timeout: Optional[float] = None
) -> List[Any]:
    """
    运行多个任务并限制并发数
    
    Args:
        tasks: 任务列表（可调用对象）
        max_concurrent: 最大并发数
        timeout: 超时时间
    
    Returns:
        结果列表
    """
    processor = AsyncBatchProcessor(max_concurrent=max_concurrent, timeout=timeout or 30.0)
    
    def execute_task(task: Callable) -> Any:
        return task()
    
    results = processor.process_batch(tasks, execute_task)
    processor.shutdown()
    
    return [r.result if r.success else None for r in results]


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    将列表分块
    
    Args:
        items: 项目列表
        chunk_size: 块大小
    
    Returns:
        分块后的列表
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

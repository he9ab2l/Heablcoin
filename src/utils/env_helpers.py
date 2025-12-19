"""
环境变量工具函数
提供类型安全的环境变量读取，避免在多个模块中重复定义。
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional
from utils.project_paths import PROJECT_ROOT


def env_str(name: str, default: str = "") -> str:
    """读取字符串类型环境变量，自动 strip 空白。"""
    v = os.getenv(name)
    if v is None:
        return default
    v = v.strip()
    return v if v else default


def env_int(name: str, default: int = 0) -> int:
    """读取整数类型环境变量。"""
    v = os.getenv(name)
    if not v:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def env_float(name: str, default: float = 0.0) -> float:
    """读取浮点类型环境变量。"""
    v = os.getenv(name)
    if not v:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def env_bool(name: str, default: bool = False) -> bool:
    """读取布尔类型环境变量。支持 1/true/yes/y/on 为真。"""
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def resolve_path(path: str, default_rel: str, base_dir: Optional[str] = None) -> str:
    """解析路径，支持相对路径和绝对路径。
    Args:
        path: 待解析的路径
        default_rel: 默认相对路径
        base_dir: 基准目录，默认为当前文件所在目录的父目录
    """
    p = (path or "").strip()
    if not p:
        p = default_rel
    if os.path.isabs(p):
        return p
    if base_dir is None:
        base_dir = str(PROJECT_ROOT)
    return os.path.join(base_dir, p)


def parse_symbols(value: str) -> list[str]:
    """解析逗号分隔的交易对列表。"""
    parts = [p.strip() for p in (value or "").split(",") if p.strip()]
    return parts
__all__ = [
    "env_str",
    "env_int",
    "env_float",
    "env_bool",
    "resolve_path",
    "parse_symbols",
]

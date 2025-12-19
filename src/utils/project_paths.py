"""
项目路径解析工具

目标：
- 不依赖模块所在目录层级（避免移动目录后路径失效）
- 以仓库根目录为基准，统一生成 reports/logs/data 等路径
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def find_repo_root(start: Optional[Path] = None) -> Path:
    """
    从指定路径向上查找包含 .git 的目录作为仓库根目录。
    找不到时回退到当前工作目录。
    """
    probe = (start or Path(__file__)).resolve()
    for parent in [probe, *probe.parents]:
        if (parent / ".git").exists():
            return parent

    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".git").exists():
            return parent

    return cwd


PROJECT_ROOT: Path = find_repo_root()


def project_path(*parts: str) -> Path:
    """以仓库根目录为基准拼接路径。"""
    return PROJECT_ROOT.joinpath(*parts)


__all__ = ["PROJECT_ROOT", "find_repo_root", "project_path"]

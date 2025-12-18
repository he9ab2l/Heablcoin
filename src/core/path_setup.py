"""
sys.path 初始化（src 分层目录结构）

目标：
- 仅将 `repo_root/src` 加入 `sys.path`
- 所有模块以“分层顶级包”方式导入：`core.* / skills.* / tools.* / utils.* / storage.*`
"""

from __future__ import annotations

import sys
from pathlib import Path


def _repo_root() -> Path:
    probe = Path(__file__).resolve()
    for parent in [probe, *probe.parents]:
        if (parent / ".git").exists():
            return parent
    # fallback: src/core/path_setup.py -> src -> repo
    return probe.parents[2]


def setup_sys_path() -> None:
    root = _repo_root()

    candidates = [root / "src"]

    for p in candidates:
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)


__all__ = ["setup_sys_path"]

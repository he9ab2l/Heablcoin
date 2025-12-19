"""

Heablcoin MCP Server (入口包装器)

================================


说明：

- 核心实现已迁移到 `src/core/server.py`

- 保留 `Heablcoin.py` 作为稳定启动入口，方便 Claude Desktop / Windsurf 继续配置此路径

"""


from __future__ import annotations


import os

import sys


def _bootstrap() -> None:

    repo_root = os.path.dirname(os.path.abspath(__file__))

    src_dir = os.path.join(repo_root, "src")

    if src_dir not in sys.path:

        sys.path.insert(0, src_dir)


    try:

        from core.path_setup import setup_sys_path


        setup_sys_path()

    except Exception:

        pass


_bootstrap()


# Re-export the server module public surface.

from core.server import *  # noqa: F401,F403


if __name__ == "__main__":

    from core.server import mcp


    mcp.run()

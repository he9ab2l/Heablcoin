############################################################
# 📘 文件说明：
# 本文件实现的功能：测试用例：验证 test_mcp_stdio_startup 相关逻辑的正确性与回归。
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
# - 依赖（标准库）：os, sys
# - 依赖（第三方）：anyio, mcp
# - 依赖（本地）：无
#
# 🕒 创建时间：2025-12-19
############################################################

import os
import sys
import anyio

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, SRC_DIR)

from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp import ClientSession


async def _run():
    params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(REPO_ROOT, "Heablcoin.py")],
        env={
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONPATH": os.pathsep.join([REPO_ROOT, SRC_DIR]),
        },
    )
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert len(tools.tools) > 0


def test_stdio_bootstrap():
    anyio.run(_run, backend="asyncio")


if __name__ == "__main__":
    # Make this test runnable under `python tests/run_tests.py integration`
    test_stdio_bootstrap()

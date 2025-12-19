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

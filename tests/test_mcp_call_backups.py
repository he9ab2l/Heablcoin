############################################################
# 📘 文件说明：
# 本文件实现的功能：单元测试：MCP 调用日志/备份（core.mcp_safety.mcp_tool_safe）
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
# - 依赖（标准库）：__future__, datetime, json, os, pathlib, shutil, sys, tempfile
# - 依赖（第三方）：无
# - 依赖（本地）：core.mcp_safety
#
# 🕒 创建时间：2025-12-19
############################################################

"""
单元测试：MCP 调用日志/备份（core.mcp_safety.mcp_tool_safe）

验证点：
1) 每次工具调用都会落盘备份（可配置目录，按天分目录）
2) 参数与返回值会按 key 名称脱敏（api_key/secret/password/token 等）
3) 失败调用也会生成备份（可选写入 traceback）

说明：本测试不依赖真实 MCP client；直接调用装饰器包装后的函数即可。
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)

from core.mcp_safety import mcp_tool_safe


def _beijing_day() -> str:
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d")


def test_backup_success_and_redaction() -> bool:
    temp_dir = tempfile.mkdtemp()
    try:
        os.environ["MCP_CALL_BACKUP_ENABLED"] = "True"
        os.environ["MCP_CALL_BACKUP_DIR"] = temp_dir
        os.environ["MCP_CALL_LOG_ENABLED"] = "False"
        os.environ["MCP_CALL_LOG_INCLUDE_ARGS"] = "True"

        @mcp_tool_safe
        def sample_tool(api_key: str, note: str = "ok") -> dict:
            return {"ok": True, "api_key": api_key, "note": note}

        result = sample_tool(api_key="sk-THIS_SHOULD_NOT_LEAK", note="hello")
        assert result.get("ok") is True

        day_dir = Path(temp_dir) / _beijing_day()
        files = sorted(day_dir.glob("*.json"))
        assert len(files) == 1, f"expected 1 backup file, got {len(files)}"

        payload = json.loads(files[0].read_text(encoding="utf-8"))
        assert payload["tool"] == "sample_tool"
        assert payload["status"] == "success"
        assert payload["kwargs"]["api_key"] == "<redacted>"
        assert payload["result"]["api_key"] == "<redacted>"
        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_backup_error_and_traceback() -> bool:
    temp_dir = tempfile.mkdtemp()
    try:
        os.environ["MCP_CALL_BACKUP_ENABLED"] = "True"
        os.environ["MCP_CALL_BACKUP_DIR"] = temp_dir
        os.environ["MCP_CALL_LOG_ENABLED"] = "False"
        os.environ["MCP_CALL_LOG_INCLUDE_ARGS"] = "True"
        os.environ["MCP_CALL_BACKUP_INCLUDE_TRACEBACK"] = "True"

        @mcp_tool_safe
        def failing_tool(password: str) -> str:
            raise ValueError("boom")

        out = failing_tool(password="super_secret")
        assert isinstance(out, str) and "工具执行失败" in out

        day_dir = Path(temp_dir) / _beijing_day()
        files = sorted(day_dir.glob("*.json"))
        assert len(files) == 1, f"expected 1 backup file, got {len(files)}"

        payload = json.loads(files[0].read_text(encoding="utf-8"))
        assert payload["tool"] == "failing_tool"
        assert payload["status"] == "error"
        assert payload["kwargs"]["password"] == "<redacted>"
        assert payload.get("traceback"), "traceback should be present when enabled"
        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_all_tests() -> bool:
    print("=" * 60)
    print("🧪 MCP Call Backup Tests")
    print("=" * 60)

    ok = True
    try:
        assert test_backup_success_and_redaction()
        print("[OK] test_backup_success_and_redaction")
    except Exception as e:
        ok = False
        print(f"[FAIL] test_backup_success_and_redaction: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    try:
        assert test_backup_error_and_traceback()
        print("[OK] test_backup_error_and_traceback")
    except Exception as e:
        ok = False
        print(f"[FAIL] test_backup_error_and_traceback: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    print("=" * 60)
    print("PASS" if ok else "FAIL")
    print("=" * 60)
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)

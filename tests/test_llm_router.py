############################################################
# 📘 文件说明：
# 本文件实现的功能：测试用例：验证 test_llm_router 相关逻辑的正确性与回归。
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
# - 依赖（第三方）：无
# - 依赖（本地）：core.orchestration.ai_router
#
# 🕒 创建时间：2025-12-19
############################################################

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)

from core.orchestration.ai_router import LLMRouter


def test_router_fallback_echo():
    router = LLMRouter()  # without keys will fall back to echo
    res = router.generate(prompt="ping", system="test", max_tokens=10)
    assert "content" in res
    assert res.get("provider") == "echo" or res.get("success") is False


def run_all_tests() -> bool:
    print("=" * 60)
    print("🧪 LLM Router Tests")
    print("=" * 60)

    ok = True
    try:
        test_router_fallback_echo()
        print("[OK] test_router_fallback_echo")
    except Exception as e:
        ok = False
        print(f"[FAIL] test_router_fallback_echo: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    print("=" * 60)
    print("PASS" if ok else "FAIL")
    print("=" * 60)
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)

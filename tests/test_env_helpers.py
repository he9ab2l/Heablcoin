############################################################
# 📘 文件说明：
# 本文件实现的功能：环境变量工具函数单元测试
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
# - 依赖（本地）：无
#
# 🕒 创建时间：2025-12-19
############################################################

"""
环境变量工具函数单元测试
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)


def run_tests():
    passed = 0
    failed = 0

    print("=" * 55)
    print("🧪 环境变量工具函数单元测试")
    print("=" * 55)
    print()

    # Test 1: env_str
    print("📝 测试1: env_str")
    try:
        from utils.env_helpers import env_str

        # Test default value
        result = env_str("NON_EXISTENT_VAR_12345", "default_value")
        assert result == "default_value", f"Expected 'default_value', got '{result}'"

        # Test with set value
        os.environ["TEST_ENV_STR"] = "  hello world  "
        result = env_str("TEST_ENV_STR", "default")
        assert result == "hello world", f"Expected 'hello world', got '{result}'"
        del os.environ["TEST_ENV_STR"]

        print("✅ 通过: env_str 正常工作")
        passed += 1
    except Exception as e:
        print(f"❌ 失败: {e}")
        failed += 1

    # Test 2: env_int
    print("\n📝 测试2: env_int")
    try:
        from utils.env_helpers import env_int

        # Test default value
        result = env_int("NON_EXISTENT_VAR_12345", 42)
        assert result == 42, f"Expected 42, got {result}"

        # Test with valid int
        os.environ["TEST_ENV_INT"] = "123"
        result = env_int("TEST_ENV_INT", 0)
        assert result == 123, f"Expected 123, got {result}"
        del os.environ["TEST_ENV_INT"]

        # Test with invalid int
        os.environ["TEST_ENV_INT_BAD"] = "not_a_number"
        result = env_int("TEST_ENV_INT_BAD", 99)
        assert result == 99, f"Expected 99 for invalid input, got {result}"
        del os.environ["TEST_ENV_INT_BAD"]

        print("✅ 通过: env_int 正常工作")
        passed += 1
    except Exception as e:
        print(f"❌ 失败: {e}")
        failed += 1

    # Test 3: env_float
    print("\n📝 测试3: env_float")
    try:
        from utils.env_helpers import env_float

        # Test default value
        result = env_float("NON_EXISTENT_VAR_12345", 3.14)
        assert result == 3.14, f"Expected 3.14, got {result}"

        # Test with valid float
        os.environ["TEST_ENV_FLOAT"] = "2.718"
        result = env_float("TEST_ENV_FLOAT", 0.0)
        assert abs(result - 2.718) < 0.001, f"Expected 2.718, got {result}"
        del os.environ["TEST_ENV_FLOAT"]

        print("✅ 通过: env_float 正常工作")
        passed += 1
    except Exception as e:
        print(f"❌ 失败: {e}")
        failed += 1

    # Test 4: env_bool
    print("\n📝 测试4: env_bool")
    try:
        from utils.env_helpers import env_bool

        # Test default value
        result = env_bool("NON_EXISTENT_VAR_12345", True)
        assert result is True, f"Expected True, got {result}"

        # Test truthy values
        for val in ["1", "true", "True", "TRUE", "yes", "YES", "y", "Y", "on", "ON"]:
            os.environ["TEST_ENV_BOOL"] = val
            result = env_bool("TEST_ENV_BOOL", False)
            assert result is True, f"Expected True for '{val}', got {result}"
            del os.environ["TEST_ENV_BOOL"]

        # Test falsy values
        for val in ["0", "false", "no", "off", "random"]:
            os.environ["TEST_ENV_BOOL"] = val
            result = env_bool("TEST_ENV_BOOL", True)
            assert result is False, f"Expected False for '{val}', got {result}"
            del os.environ["TEST_ENV_BOOL"]

        print("✅ 通过: env_bool 正常工作")
        passed += 1
    except Exception as e:
        print(f"❌ 失败: {e}")
        failed += 1

    # Test 5: parse_symbols
    print("\n📝 测试5: parse_symbols")
    try:
        from utils.env_helpers import parse_symbols

        # Test normal case
        result = parse_symbols("BTC/USDT, ETH/USDT, SOL/USDT")
        assert result == ["BTC/USDT", "ETH/USDT", "SOL/USDT"], f"Unexpected result: {result}"

        # Test empty string
        result = parse_symbols("")
        assert result == [], f"Expected empty list, got {result}"

        # Test with extra spaces
        result = parse_symbols("  BTC/USDT  ,  ETH/USDT  ")
        assert result == ["BTC/USDT", "ETH/USDT"], f"Unexpected result: {result}"

        print("✅ 通过: parse_symbols 正常工作")
        passed += 1
    except Exception as e:
        print(f"❌ 失败: {e}")
        failed += 1

    # Summary
    print()
    print("=" * 55)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    print("=" * 55)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

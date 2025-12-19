############################################################
# 📘 文件说明：
# 本文件实现的功能：测试用例：验证 test_risk_management 相关逻辑的正确性与回归。
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
# - 依赖（本地）：utils.risk_management
#
# 🕒 创建时间：2025-12-19
############################################################

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)

from utils.risk_management import PositionSize, calculate_position_size, trailing_stop


def test_position_size_basic():
    print("\n📝 测试1: 风控-基础仓位计算")
    try:
        ps = calculate_position_size(balance=1000, price=100, stop_distance=10, risk_per_trade=0.02)
        assert isinstance(ps, PositionSize)
        assert abs(ps.quantity - 2.0) < 1e-9
        assert abs(ps.notional - 200.0) < 1e-9
        print("✅ 通过: 基础仓位计算")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_position_size_fixed_notional():
    print("\n📝 测试2: 风控-固定名义金额")
    try:
        ps = calculate_position_size(balance=1000, price=100, stop_distance=10, use_fixed_notional=500)
        assert abs(ps.quantity - 5.0) < 1e-9
        assert abs(ps.notional - 500.0) < 1e-9
        print("✅ 通过: 固定名义金额")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_position_size_invalid_inputs():
    print("\n📝 测试3: 风控-非法输入")
    try:
        ok = False
        try:
            calculate_position_size(balance=0, price=100, stop_distance=10)
        except ValueError:
            ok = True
        assert ok

        ok = False
        try:
            calculate_position_size(balance=1000, price=100, stop_distance=10, risk_per_trade=1.0)
        except ValueError:
            ok = True
        assert ok

        ok = False
        try:
            calculate_position_size(balance=1000, price=100, stop_distance=10, use_fixed_notional=100, use_fixed_quantity=1)
        except ValueError:
            ok = True
        assert ok

        print("✅ 通过: 非法输入校验")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_trailing_stop():
    print("\n📝 测试4: 风控-追踪止损")
    try:
        stop = trailing_stop(current_price=105, peak_price=110, trail_percent=0.05)
        assert abs(stop - 104.5) < 1e-9

        ok = False
        try:
            trailing_stop(current_price=105, peak_price=110, trail_percent=1.0)
        except ValueError:
            ok = True
        assert ok

        print("✅ 通过: 追踪止损")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def run_all_tests():
    print("=" * 60)
    print("🧪 风险管理模块单元测试")
    print("=" * 60)

    tests = [
        test_position_size_basic,
        test_position_size_fixed_notional,
        test_position_size_invalid_inputs,
        test_trailing_stop,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

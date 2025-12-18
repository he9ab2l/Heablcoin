import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)

from utils.backtesting import run_backtest


def test_backtest_basic():
    print("\n📝 测试1: 回测-基础逻辑")
    try:
        prices = [100, 110, 105, 120]
        signals = [0, 1, 1, 0]
        total_return, win_rate = run_backtest(prices, signals)
        assert isinstance(total_return, float)
        assert isinstance(win_rate, float)
        assert win_rate >= 0
        print("✅ 通过: 回测基础逻辑")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_backtest_length_mismatch():
    print("\n📝 测试2: 回测-长度不一致")
    try:
        ok = False
        try:
            run_backtest([1, 2], [1])
        except ValueError:
            ok = True
        assert ok
        print("✅ 通过: 长度不一致抛异常")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def run_all_tests():
    print("=" * 60)
    print("🧪 回测模块单元测试")
    print("=" * 60)

    tests = [
        test_backtest_basic,
        test_backtest_length_mismatch,
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

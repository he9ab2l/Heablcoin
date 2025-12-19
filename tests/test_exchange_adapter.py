import os
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)
from utils.exchange_adapter import BinanceAdapter, BybitAdapter, OKXAdapter


def _is_ccxt_available() -> bool:
    try:
        import ccxt  # noqa: F401


        return True
    except Exception:
        return False


def test_okx_stub_raises():
    print("\n📝 测试1: 交易所适配器-OKX桩")
    try:
        okx = OKXAdapter()
        ok = False
        try:
            okx.get_ticker("BTC/USDT")
        except NotImplementedError:
            ok = True
        assert ok
        print("✅ 通过: OKX桩按预期抛 NotImplementedError")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_bybit_stub_raises():
    print("\n📝 测试2: 交易所适配器-Bybit桩")
    try:
        bybit = BybitAdapter()
        ok = False
        try:
            bybit.place_order("BTC/USDT", "buy", 0.1)
        except NotImplementedError:
            ok = True
        assert ok
        print("✅ 通过: Bybit桩按预期抛 NotImplementedError")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_binance_without_ccxt_behavior():
    print("\n📝 测试3: 交易所适配器-Binance无ccxt行为")
    try:
        b = BinanceAdapter()
        if _is_ccxt_available() and getattr(b, "client", None) is not None:
            print("✅ 通过: ccxt 可用时跳过真实行情调用（避免外部网络）")
            return True
        ok = False
        try:
            b.get_ticker("BTC/USDT")
        except NotImplementedError:
            ok = True
        except Exception:
            ok = True
        assert ok
        print("✅ 通过: ccxt 不可用/无client时不静默成功")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def run_all_tests():
    print("=" * 60)
    print("🧪 交易所适配器模块单元测试")
    print("=" * 60)
    tests = [
        test_okx_stub_raises,
        test_bybit_stub_raises,
        test_binance_without_ccxt_behavior,
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

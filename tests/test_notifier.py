import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)

from utils.notifier import ConsoleChannel, Notifier, TelegramChannel


def _is_telegram_available() -> bool:
    try:
        import telegram  # noqa: F401

        return True
    except Exception:
        return False


def test_notifier_console_channel():
    print("\n📝 测试1: Notifier-控制台通道")
    try:
        notifier = Notifier([ConsoleChannel()])
        notifier.notify("test", "hello")
        print("✅ 通过: 控制台通道通知")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_telegram_channel_import_behavior():
    print("\n📝 测试2: Notifier-Telegram通道依赖行为")
    try:
        if _is_telegram_available():
            ch = TelegramChannel(bot_token="x", chat_id="y")
            assert ch is not None
            print("✅ 通过: Telegram依赖存在时可构造通道对象")
        else:
            ok = False
            try:
                TelegramChannel(bot_token="x", chat_id="y")
            except ImportError:
                ok = True
            assert ok
            print("✅ 通过: Telegram依赖缺失时抛 ImportError")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def run_all_tests():
    print("=" * 60)
    print("🧪 通知模块单元测试")
    print("=" * 60)

    tests = [
        test_notifier_console_channel,
        test_telegram_channel_import_behavior,
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

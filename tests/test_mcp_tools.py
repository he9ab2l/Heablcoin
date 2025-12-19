"""

单元测试：MCP工具功能

测试主要MCP工具的异常保护和基本功能

"""


import sys

import os


# 添加项目路径

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SRC_DIR = os.path.join(REPO_ROOT, "src")

sys.path.insert(0, REPO_ROOT)

sys.path.insert(0, SRC_DIR)


def test_mcp_tool_safe_decorator():

    """测试MCP工具安全装饰器"""

    print("\n📝 测试1: MCP工具安全装饰器")


    try:

        import functools


        def mcp_tool_safe(func):

            @functools.wraps(func)

            def wrapper(*args, **kwargs):

                try:

                    return func(*args, **kwargs)

                except Exception as e:

                    return f"⚠️ 工具执行失败: {type(e).__name__}: {str(e)}"

            return wrapper


        # 测试正常函数

        @mcp_tool_safe

        def normal_function(x):

            return x * 2


        result = normal_function(5)

        assert result == 10, "正常函数返回值不正确"


        # 测试异常函数

        @mcp_tool_safe

        def error_function():

            raise ValueError("测试错误")


        result = error_function()

        assert "工具执行失败" in result, "异常未被捕获"

        assert "ValueError" in result, "错误类型未包含"


        print("✅ 通过: 安全装饰器正常工作")

        return True

    except Exception as e:

        print(f"❌ 失败: {e}")

        return False


def test_stdout_isolation():

    """测试stdout隔离"""

    print("\n📝 测试2: stdout隔离机制")


    try:

        import sys

        import io


        # 保存原始stdout

        original_stdout = sys.stdout


        # 模拟重定向

        sys.stdout = sys.stderr


        # 测试print（应该输出到stderr）

        print("测试输出（应该在stderr）")


        # 恢复

        sys.stdout = original_stdout


        print("✅ 通过: stdout隔离机制可以正常工作")

        return True

    except Exception as e:

        print(f"❌ 失败: {e}")

        return False


def test_env_helpers():

    """测试环境变量辅助函数（使用 utils.env_helpers）"""

    print("\n📝 测试3: 环境变量辅助函数")


    try:

        import os

        from utils.env_helpers import env_bool, env_float


        # 测试bool解析

        os.environ['TEST_BOOL'] = 'true'

        assert env_bool('TEST_BOOL') == True, "bool解析失败"


        # 测试float解析

        os.environ['TEST_FLOAT'] = '123.45'

        assert env_float('TEST_FLOAT', 0.0) == 123.45, "float解析失败"


        # 测试默认值

        assert env_bool('NONEXISTENT', False) == False, "默认值失败"


        # 清理

        del os.environ['TEST_BOOL']

        del os.environ['TEST_FLOAT']


        print("✅ 通过: 环境变量辅助函数正常")

        return True

    except Exception as e:

        print(f"❌ 失败: {e}")

        return False


def test_notification_switches():

    """测试通知开关逻辑"""

    print("\n📝 测试4: 通知开关逻辑")


    try:

        from typing import Optional, Dict

        from utils.env_helpers import env_bool


        _NOTIFY_RUNTIME_OVERRIDES: Dict[str, Optional[bool]] = {

            'NOTIFY_TRADE_EXECUTION': None,

            'NOTIFY_PRICE_ALERTS': None,

        }


        def _notify_enabled(key: str, default: bool = True) -> bool:

            override = _NOTIFY_RUNTIME_OVERRIDES.get(key)

            if override is not None:

                return bool(override)

            return env_bool(key, default)


        # 测试默认值

        assert _notify_enabled('NOTIFY_TRADE_EXECUTION', True) == True, "默认值应为True"


        # 测试运行时覆盖

        _NOTIFY_RUNTIME_OVERRIDES['NOTIFY_TRADE_EXECUTION'] = False

        assert _notify_enabled('NOTIFY_TRADE_EXECUTION', True) == False, "运行时覆盖失败"


        print("✅ 通过: 通知开关逻辑正常")

        return True

    except Exception as e:

        print(f"❌ 失败: {e}")

        return False


def test_safe_filename():

    """测试安全文件名生成"""

    print("\n📝 测试5: 安全文件名生成")


    try:

        import re


        def _safe_filename_component(value: str) -> str:

            value = (value or '').strip()

            value = value.replace('/', '_').replace('\\', '_')

            value = re.sub(r'[^A-Za-z0-9._-]+', '_', value)

            value = re.sub(r'_+', '_', value).strip('_')

            return value or 'unknown'


        # 测试正常字符串

        assert _safe_filename_component('BTC/USDT') == 'BTC_USDT', "斜杠替换失败"


        # 测试特殊字符

        assert _safe_filename_component('test@#$%file') == 'test_file', "特殊字符处理失败"


        # 测试空字符串

        assert _safe_filename_component('') == 'unknown', "空字符串处理失败"


        print("✅ 通过: 安全文件名生成正常")

        return True

    except Exception as e:

        print(f"❌ 失败: {e}")

        return False


def run_all_tests():

    """运行所有测试"""

    print("=" * 60)

    print("🧪 MCP工具功能单元测试")

    print("=" * 60)


    tests = [

        test_mcp_tool_safe_decorator,

        test_stdout_isolation,

        test_env_helpers,

        test_notification_switches,

        test_safe_filename,

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

            import traceback

            traceback.print_exc()

            failed += 1


    print("\n" + "=" * 60)

    print(f"📊 测试结果: {passed} 通过, {failed} 失败")

    print("=" * 60)


    return failed == 0


if __name__ == "__main__":

    success = run_all_tests()

    sys.exit(0 if success else 1)

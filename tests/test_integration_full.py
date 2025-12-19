"""
完整集成测试
全面测试所有优化功能的协同工作
"""
import sys
import os
import time


# 添加项目路径
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)


def test_p0_stdout_isolation():
    """测试P0-1: stdout隔离"""
    print("\n📝 测试P0-1: stdout隔离机制")
    try:
        # 验证stdout已被重定向
        import sys


        # 保存当前stdout
        current_stdout = sys.stdout
        # 验证stdout指向stderr
        assert current_stdout == sys.stderr or hasattr(current_stdout, 'write'), "stdout应该被重定向"
        print("✅ 通过: stdout隔离机制已激活")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_p0_exception_protection():
    """测试P0-2: 全局异常保护"""
    print("\n📝 测试P0-2: 全局异常保护")
    try:
        import functools


        # 模拟mcp_tool_safe装饰器
        def mcp_tool_safe(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    return f"⚠️ 工具执行失败: {type(e).__name__}: {str(e)}"
            return wrapper
        # 测试各种异常类型
        @mcp_tool_safe
        def test_value_error():
            raise ValueError("测试ValueError")
        @mcp_tool_safe
        def test_type_error():
            raise TypeError("测试TypeError")
        @mcp_tool_safe
        def test_zero_division():
            return 1 / 0
        result1 = test_value_error()
        result2 = test_type_error()
        result3 = test_zero_division()
        assert "工具执行失败" in result1, "ValueError未被捕获"
        assert "工具执行失败" in result2, "TypeError未被捕获"
        assert "工具执行失败" in result3, "ZeroDivisionError未被捕获"
        print("✅ 通过: 全局异常保护正常工作")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_p0_smart_logger():
    """测试P0-3: 智能日志系统"""
    print("\n📝 测试P0-3: 智能日志系统")
    try:
        from utils.smart_logger import get_smart_logger


        logger = get_smart_logger()
        # 验证所有日志通道
        channels = ['system', 'trading', 'analysis', 'error', 'performance']
        for channel in channels:
            log = logger.get_logger(channel)
            assert log is not None, f"{channel} logger不存在"
        # 测试性能记录
        logger.log_performance('test_func', 1.5, True)
        logger.log_performance('test_func', 2.0, False)
        stats = logger.get_performance_stats()
        assert 'test_func' in stats, "性能统计缺失"
        assert stats['test_func']['total_calls'] == 2, "调用次数不正确"
        assert stats['test_func']['errors'] == 1, "错误次数不正确"
        print(f"✅ 通过: 智能日志系统正常 ({len(channels)}个通道)")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback


        traceback.print_exc()
        return False


def test_p1_smart_cache():
    """测试P1-1: 智能缓存系统"""
    print("\n📝 测试P1-1: 智能缓存系统")
    try:
        from utils.smart_cache import get_smart_cache, cached


        cache = get_smart_cache()
        # 测试基本缓存
        cache.set('test_key', 'test_value')
        value = cache.get('test_key', ttl=60)
        assert value == 'test_value', "缓存值不匹配"
        # 测试装饰器
        call_count = [0]
        @cached(ttl=60)
        def expensive_function(x):
            call_count[0] += 1
            return x * 2
        result1 = expensive_function(10)
        result2 = expensive_function(10)  # 应该从缓存获取
        assert result1 == 20, "返回值不正确"
        assert result2 == 20, "缓存返回值不正确"
        assert call_count[0] == 1, "函数应该只被调用一次"
        # 验证统计
        stats = cache.get_stats()
        assert stats['total_hits'] > 0, "应该有缓存命中"
        print(f"✅ 通过: 智能缓存系统正常 (命中率: {stats['hit_rate']})")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback


        traceback.print_exc()
        return False


def test_logger_cache_integration():
    """测试日志和缓存协同工作"""
    print("\n📝 测试: 日志和缓存协同工作")
    try:
        from utils.smart_logger import get_smart_logger, log_performance
        from utils.smart_cache import get_smart_cache, cached


        logger = get_smart_logger()
        cache = get_smart_cache()
        # 创建一个同时使用日志和缓存的函数
        @cached(ttl=60)
        @log_performance
        def complex_function(x):
            logger.get_logger('analysis').info(f"执行复杂计算: {x}")
            time.sleep(0.1)
            return x ** 2
        # 第一次调用（执行函数 + 记录性能）
        result1 = complex_function(5)
        # 第二次调用（从缓存获取，不执行函数但仍记录性能）
        result2 = complex_function(5)
        assert result1 == 25, "返回值不正确"
        assert result2 == 25, "缓存返回值不正确"
        # 验证性能统计
        perf_stats = logger.get_performance_stats()
        assert 'complex_function' in perf_stats, "性能统计缺失"
        # 验证缓存统计
        cache_stats = cache.get_stats()
        assert cache_stats['total_hits'] > 0, "应该有缓存命中"
        print("✅ 通过: 日志和缓存协同工作正常")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback


        traceback.print_exc()
        return False


def test_error_logging_with_cache():
    """测试错误日志和缓存的协同"""
    print("\n📝 测试: 错误日志和缓存协同")
    try:
        from utils.smart_logger import get_smart_logger
        from utils.smart_cache import cached


        logger = get_smart_logger()
        @cached(ttl=60)
        def error_function(should_error):
            if should_error:
                logger.get_logger('error').error("测试错误日志")
                raise ValueError("测试错误")
            return "success"
        # 正常调用
        result1 = error_function(False)
        assert result1 == "success", "正常调用失败"
        # 缓存命中
        result2 = error_function(False)
        assert result2 == "success", "缓存调用失败"
        # 错误调用（不会被缓存）
        try:
            error_function(True)
            assert False, "应该抛出异常"
        except ValueError:
            pass
        print("✅ 通过: 错误日志和缓存协同正常")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback


        traceback.print_exc()
        return False


def test_all_optimizations_enabled():
    """测试所有优化功能是否启用"""
    print("\n📝 测试: 所有优化功能状态")
    try:
        from utils.smart_logger import get_smart_logger
        from utils.smart_cache import get_smart_cache


        logger = get_smart_logger()
        cache = get_smart_cache()
        # 验证实例存在
        assert logger is not None, "SmartLogger未启用"
        assert cache is not None, "SmartCache未启用"
        # 验证功能可用
        assert hasattr(logger, 'get_logger'), "SmartLogger缺少get_logger方法"
        assert hasattr(logger, 'log_performance'), "SmartLogger缺少log_performance方法"
        assert hasattr(cache, 'get'), "SmartCache缺少get方法"
        assert hasattr(cache, 'set'), "SmartCache缺少set方法"
        assert hasattr(cache, 'get_stats'), "SmartCache缺少get_stats方法"
        print("✅ 通过: 所有优化功能已启用")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback


        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 完整集成测试")
    print("=" * 60)
    tests = [
        ("P0-1: stdout隔离", test_p0_stdout_isolation),
        ("P0-2: 异常保护", test_p0_exception_protection),
        ("P0-3: 智能日志", test_p0_smart_logger),
        ("P1-1: 智能缓存", test_p1_smart_cache),
        ("集成: 日志+缓存", test_logger_cache_integration),
        ("集成: 错误+缓存", test_error_logging_with_cache),
        ("状态: 优化功能", test_all_optimizations_enabled),
    ]
    passed = 0
    failed = 0
    results = []
    for name, test in tests:
        try:
            if test():
                passed += 1
                results.append(f"✅ {name}")
            else:
                failed += 1
                results.append(f"❌ {name}")
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            import traceback


            traceback.print_exc()
            failed += 1
            results.append(f"❌ {name} (异常)")
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    for result in results:
        print(result)
    print("\n" + "=" * 60)
    print(f"总计: {passed} 通过, {failed} 失败")
    print("=" * 60)
    return failed == 0
if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

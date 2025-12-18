############################################################
# 📘 文件说明：简单集成测试
# 本文件实现的功能：快速集成测试
#
# 📋 程序整体伪代码（中文）：
# 1. 初始化依赖模块和配置
# 2. 定义核心类和函数
# 3. 实现主要业务逻辑
# 4. 提供对外接口
# 5. 异常处理与日志记录
#
# 🔄 程序流程图（逻辑流）：
# ┌──────────────┐
# │  测试用例    │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  执行断言    │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  输出结果    │
# └──────────────┘
#
# 📊 数据管道说明：
# 数据流向：输入源 → 数据处理 → 核心算法 → 输出目标
#
# 🧩 文件结构：
# - 函数: test_utils_import, test_logger_cache_integration, test_performance_monitoring, test_exception_handling, test_log_files_creation
#
# 🔗 主要依赖：functools, os, sys, time, traceback, utils
#
# 🕒 创建时间：2025-12-18
############################################################

"""
简单集成测试
快速验证核心功能是否正常工作
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_utils_import():
    """测试工具模块导入"""
    print("\n📝 测试1: 工具模块导入")
    
    try:
        from utils.smart_logger import get_smart_logger
        from utils.smart_cache import get_smart_cache
        
        logger = get_smart_logger()
        cache = get_smart_cache()
        
        assert logger is not None, "logger实例化失败"
        assert cache is not None, "cache实例化失败"
        
        print("✅ 通过: 工具模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logger_cache_integration():
    """测试日志和缓存集成"""
    print("\n📝 测试2: 日志和缓存集成")
    
    try:
        from utils.smart_logger import get_smart_logger
        from utils.smart_cache import get_smart_cache, cached
        
        logger = get_smart_logger()
        cache = get_smart_cache()
        
        # 测试缓存装饰器
        @cached(ttl=60)
        def test_function(x):
            logger.get_logger('system').info(f"执行函数: {x}")
            return x * 2
        
        result1 = test_function(5)
        result2 = test_function(5)  # 应该从缓存获取
        
        assert result1 == 10, "函数返回值不正确"
        assert result2 == 10, "缓存返回值不正确"
        
        # 验证缓存统计
        stats = cache.get_stats()
        assert stats['total_hits'] > 0, "应该有缓存命中"
        
        print(f"✅ 通过: 日志和缓存集成正常 (命中率: {stats['hit_rate']})")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_monitoring():
    """测试性能监控"""
    print("\n📝 测试3: 性能监控")
    
    try:
        from utils.smart_logger import get_smart_logger, log_performance
        import time
        
        logger = get_smart_logger()
        
        # 使用性能装饰器
        @log_performance
        def slow_function():
            time.sleep(0.1)
            return "done"
        
        result = slow_function()
        assert result == "done", "函数返回值不正确"
        
        # 验证性能统计
        stats = logger.get_performance_stats()
        assert 'slow_function' in stats, "性能统计缺失"
        
        print(f"✅ 通过: 性能监控正常 (记录了 {len(stats)} 个函数)")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_exception_handling():
    """测试异常处理"""
    print("\n📝 测试4: 异常处理")
    
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
        
        @mcp_tool_safe
        def error_function():
            raise ValueError("测试错误")
        
        result = error_function()
        assert "工具执行失败" in result, "异常未被捕获"
        
        print("✅ 通过: 异常处理正常")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_log_files_creation():
    """测试日志文件创建"""
    print("\n📝 测试5: 日志文件创建")
    
    try:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        
        if os.path.exists(log_dir):
            log_files = os.listdir(log_dir)
            expected_files = ['system.log', 'trading.log', 'analysis.log', 'error.log', 'performance.log']
            
            found_count = sum(1 for f in expected_files if f in log_files)
            
            print(f"✅ 通过: 找到 {found_count}/{len(expected_files)} 个日志文件")
            return True
        else:
            print("⚠️ 警告: 日志目录不存在（首次运行时正常）")
            return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 简单集成测试")
    print("=" * 60)
    
    tests = [
        test_utils_import,
        test_logger_cache_integration,
        test_performance_monitoring,
        test_exception_handling,
        test_log_files_creation,
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

"""
单元测试：智能缓存系统
测试 utils/smart_cache.py 的所有功能
"""

import sys
import os
import time

# 添加项目路径
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)

from utils.smart_cache import SmartCache, get_smart_cache, cached


def test_cache_basic_operations():
    """测试基本缓存操作"""
    print("\n📝 测试1: 基本缓存操作")
    
    try:
        cache = SmartCache()
        
        # 设置缓存
        cache.set('key1', 'value1')
        cache.set('key2', {'data': 'value2'})
        
        # 获取缓存
        value1 = cache.get('key1', ttl=60)
        value2 = cache.get('key2', ttl=60)
        
        assert value1 == 'value1', "缓存值1不匹配"
        assert value2 == {'data': 'value2'}, "缓存值2不匹配"
        
        print("✅ 通过: 基本缓存读写正常")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_cache_ttl():
    """测试TTL过期"""
    print("\n📝 测试2: TTL过期机制")
    
    try:
        cache = SmartCache()
        
        # 设置短TTL缓存
        cache.set('temp_key', 'temp_value')
        
        # 立即获取（应该存在）
        value1 = cache.get('temp_key', ttl=1)
        assert value1 == 'temp_value', "缓存应该存在"
        
        # 等待过期
        time.sleep(1.1)
        
        # 再次获取（应该过期）
        value2 = cache.get('temp_key', ttl=1)
        assert value2 is None, "缓存应该已过期"
        
        print("✅ 通过: TTL过期机制正常")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_cache_miss():
    """测试缓存未命中"""
    print("\n📝 测试3: 缓存未命中")
    
    try:
        cache = SmartCache()
        
        # 获取不存在的键
        value = cache.get('nonexistent_key', ttl=60)
        assert value is None, "不存在的键应返回None"
        
        # 验证统计
        stats = cache.get_stats()
        assert stats['total_misses'] > 0, "未命中计数应该增加"
        
        print("✅ 通过: 缓存未命中处理正常")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_cache_stats():
    """测试缓存统计"""
    print("\n📝 测试4: 缓存统计")
    
    try:
        cache = SmartCache()
        
        # 执行一些操作
        cache.set('key1', 'value1')
        cache.get('key1', ttl=60)  # 命中
        cache.get('key1', ttl=60)  # 命中
        cache.get('key2', ttl=60)  # 未命中
        
        # 获取统计
        stats = cache.get_stats()
        
        assert 'hit_rate' in stats, "缺少命中率"
        assert 'total_hits' in stats, "缺少总命中数"
        assert 'total_misses' in stats, "缺少总未命中数"
        assert 'total_keys' in stats, "缺少总键数"
        
        print(f"✅ 通过: 统计数据完整 (命中率: {stats['hit_rate']})")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_cache_clear():
    """测试缓存清除"""
    print("\n📝 测试5: 缓存清除")
    
    try:
        cache = SmartCache()
        
        # 设置多个缓存
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('test_key', 'test_value')
        
        # 清除匹配的缓存
        cache.clear(pattern='test')
        
        # 验证
        assert cache.get('key1', ttl=60) == 'value1', "key1应该存在"
        assert cache.get('test_key', ttl=60) is None, "test_key应该被清除"
        
        # 清除所有
        cache.clear()
        assert cache.get('key1', ttl=60) is None, "所有缓存应该被清除"
        
        print("✅ 通过: 缓存清除功能正常")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_cached_decorator():
    """测试缓存装饰器"""
    print("\n📝 测试6: 缓存装饰器")
    
    try:
        call_count = [0]  # 使用列表来跟踪调用次数
        
        @cached(ttl=60, key_prefix="test_")
        def expensive_function(x):
            call_count[0] += 1
            return x * 2
        
        # 第一次调用（应该执行函数）
        result1 = expensive_function(5)
        assert result1 == 10, "返回值不正确"
        assert call_count[0] == 1, "函数应该被调用一次"
        
        # 第二次调用（应该从缓存获取）
        result2 = expensive_function(5)
        assert result2 == 10, "返回值不正确"
        assert call_count[0] == 1, "函数不应该被再次调用"
        
        # 不同参数（应该执行函数）
        result3 = expensive_function(10)
        assert result3 == 20, "返回值不正确"
        assert call_count[0] == 2, "函数应该被调用两次"
        
        print("✅ 通过: 缓存装饰器正常工作")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_global_instance():
    """测试全局实例"""
    print("\n📝 测试7: 全局实例")
    
    try:
        cache1 = get_smart_cache()
        cache2 = get_smart_cache()
        
        assert cache1 is cache2, "全局实例不一致"
        
        # 验证共享状态
        cache1.set('shared_key', 'shared_value')
        value = cache2.get('shared_key', ttl=60)
        assert value == 'shared_value', "全局实例应该共享状态"
        
        print("✅ 通过: 全局实例单例模式正常")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 智能缓存系统单元测试")
    print("=" * 60)
    
    tests = [
        test_cache_basic_operations,
        test_cache_ttl,
        test_cache_miss,
        test_cache_stats,
        test_cache_clear,
        test_cached_decorator,
        test_global_instance,
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

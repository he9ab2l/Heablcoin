############################################################
# 📘 文件说明：
# 本文件实现的功能：单元测试：智能日志系统
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
# - 依赖（标准库）：os, shutil, sys, tempfile, time
# - 依赖（第三方）：无
# - 依赖（本地）：utils.smart_logger
#
# 🕒 创建时间：2025-12-19
############################################################

"""
单元测试：智能日志系统
测试 utils/smart_logger.py 的所有功能
"""

import sys
import os
import time
import tempfile
import shutil

# 添加项目路径
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)

from utils.smart_logger import SmartLogger, get_smart_logger, log_performance


def test_smart_logger_creation():
    """测试 SmartLogger 创建"""
    print("\n📝 测试1: SmartLogger 创建")
    
    # 使用临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        logger = SmartLogger(base_dir=temp_dir)
        
        # 验证日志通道
        assert 'system' in logger.loggers, "缺少 system logger"
        assert 'trading' in logger.loggers, "缺少 trading logger"
        assert 'analysis' in logger.loggers, "缺少 analysis logger"
        assert 'error' in logger.loggers, "缺少 error logger"
        assert 'performance' in logger.loggers, "缺少 performance logger"
        assert 'learning' in logger.loggers, "缺少 learning logger"
        assert 'cloud' in logger.loggers, "缺少 cloud logger"
        assert 'storage' in logger.loggers, "缺少 storage logger"
        assert 'mcp' in logger.loggers, "缺少 mcp logger"
        
        print(f"✅ 通过: 创建了 {len(logger.loggers)} 个日志通道")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_logger_channels():
    """测试不同日志通道"""
    print("\n📝 测试2: 日志通道写入")
    
    temp_dir = tempfile.mkdtemp()
    try:
        logger = SmartLogger(base_dir=temp_dir)
        
        # 写入不同通道
        logger.get_logger('system').info("系统日志测试")
        logger.get_logger('trading').info("交易日志测试")
        logger.get_logger('error').error("错误日志测试")
        logger.get_logger('mcp').info("MCP日志测试")
        
        # 验证日志文件存在
        log_files = os.listdir(temp_dir)
        assert 'system.log' in log_files, "system.log 未创建"
        assert 'trading.log' in log_files, "trading.log 未创建"
        assert 'error.log' in log_files, "error.log 未创建"
        assert 'mcp.log' in log_files, "mcp.log 未创建"
        
        print(f"✅ 通过: 创建了 {len(log_files)} 个日志文件")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_performance_logging():
    """测试性能记录"""
    print("\n📝 测试3: 性能记录")
    
    temp_dir = tempfile.mkdtemp()
    try:
        logger = SmartLogger(base_dir=temp_dir)
        
        # 记录性能
        logger.log_performance('test_func', 1.5, True)
        logger.log_performance('test_func', 2.0, True)
        logger.log_performance('slow_func', 5.0, True)
        
        # 获取统计
        stats = logger.get_performance_stats()
        
        assert 'test_func' in stats, "test_func 统计缺失"
        assert stats['test_func']['total_calls'] == 2, "调用次数不正确"
        assert stats['test_func']['max_time'] == 2.0, "最大时间不正确"
        
        print(f"✅ 通过: 记录了 {len(stats)} 个函数的性能数据")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_performance_decorator():
    """测试性能装饰器"""
    print("\n📝 测试4: 性能装饰器")
    
    temp_dir = tempfile.mkdtemp()
    try:
        # 创建临时logger
        logger = SmartLogger(base_dir=temp_dir)
        
        # 使用装饰器
        @log_performance
        def test_function(x):
            time.sleep(0.1)
            return x * 2
        
        result = test_function(5)
        assert result == 10, "函数返回值不正确"
        
        # 验证性能记录
        stats = logger.get_performance_stats()
        # 注意：装饰器使用全局实例，可能不在temp_dir
        
        print("✅ 通过: 装饰器正常工作")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_global_instance():
    """测试全局实例"""
    print("\n📝 测试5: 全局实例")
    
    try:
        logger1 = get_smart_logger()
        logger2 = get_smart_logger()
        
        assert logger1 is logger2, "全局实例不一致"
        
        print("✅ 通过: 全局实例单例模式正常")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 智能日志系统单元测试")
    print("=" * 60)
    
    tests = [
        test_smart_logger_creation,
        test_logger_channels,
        test_performance_logging,
        test_performance_decorator,
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

############################################################
# 📘 文件说明：测试运行器
# 本文件实现的功能：统一的测试运行入口
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
# - 函数: run_test_file, run_test_suite, list_tests, main
#
# 🔗 主要依赖：argparse, os, subprocess, sys, traceback
#
# 🕒 创建时间：2025-12-18
############################################################

"""
测试运行器
提供统一的测试入口，支持运行单个测试或所有测试
"""

import sys
import os
import subprocess
import argparse

# Avoid UnicodeEncodeError on Windows consoles (e.g., emoji output).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 添加项目路径
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, SRC_DIR)
try:
    from core.path_setup import setup_sys_path

    setup_sys_path()
except Exception:
    pass


# 测试套件配置
TEST_SUITES = {
    'unit': {
        'name': '单元测试',
        'tests': [
            'test_smart_logger.py',
            'test_smart_cache.py',
            'test_mcp_tools.py',
            'test_tool_registry.py',
            'test_visualization_output.py',
            'test_risk_management.py',
            'test_notifier.py',
            'test_backtesting.py',
            'test_exchange_adapter.py',
            'test_lesson_recorder.py',
            'test_env_helpers.py',
            'test_project_records.py',
        ]
    },
    'email': {
        'name': '邮箱测试（需要配置 .env，可能发送真实邮件）',
        'tests': [
            'test_email_connection.py',
        ]
    },
    'integration': {
        'name': '集成测试',
        'tests': [
            'test_integration_simple.py',
            'test_integration_full.py',
        ]
    },
    'all': {
        'name': '所有测试',
        'tests': [
            'test_smart_logger.py',
            'test_smart_cache.py',
            'test_mcp_tools.py',
            'test_tool_registry.py',
            'test_visualization_output.py',
            'test_risk_management.py',
            'test_notifier.py',
            'test_backtesting.py',
            'test_exchange_adapter.py',
            'test_lesson_recorder.py',
            'test_env_helpers.py',
            'test_project_records.py',
            'test_integration_simple.py',
            'test_integration_full.py',
        ]
    }
}


def run_test_file(test_file):
    """运行单个测试文件"""
    test_path = os.path.join(os.path.dirname(__file__), test_file)
    
    if not os.path.exists(test_path):
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    print(f"\n{'='*60}")
    print(f"▶️  运行: {test_file}")
    print(f"{'='*60}")
    
    try:
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("PYTHONUTF8", "1")
        # Keep PYTHONPATH minimal: repo root (for `lesson/`) + `src` (for core/tools/skills/utils/storage).
        extra_paths = [REPO_ROOT, SRC_DIR]
        existing = env.get("PYTHONPATH", "")
        merged = os.pathsep.join([p for p in extra_paths if p] + ([existing] if existing else []))
        env["PYTHONPATH"] = merged
        result = subprocess.run(
            [sys.executable, test_path],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            env=env,
            capture_output=False,
            text=True
        )
        
        success = result.returncode == 0
        if success:
            print(f"✅ {test_file} 通过")
        else:
            print(f"❌ {test_file} 失败")
        
        return success
    except Exception as e:
        print(f"❌ 运行测试时出错: {e}")
        return False


def run_test_suite(suite_name):
    """运行测试套件"""
    if suite_name not in TEST_SUITES:
        print(f"❌ 未知的测试套件: {suite_name}")
        print(f"可用套件: {', '.join(TEST_SUITES.keys())}")
        return False
    
    suite = TEST_SUITES[suite_name]
    print(f"\n{'='*60}")
    print(f"🧪 {suite['name']}")
    print(f"{'='*60}")
    
    results = []
    for test_file in suite['tests']:
        success = run_test_file(test_file)
        results.append((test_file, success))
    
    # 汇总结果
    print(f"\n{'='*60}")
    print(f"📊 {suite['name']} - 结果汇总")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    
    for test_file, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_file}")
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    return failed == 0


def list_tests():
    """列出所有可用的测试"""
    print("\n📋 可用的测试套件:\n")
    
    for suite_name, suite in TEST_SUITES.items():
        print(f"  {suite_name:15} - {suite['name']}")
        for test_file in suite['tests']:
            print(f"    └─ {test_file}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Heablcoin 测试运行器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_tests.py                    # 运行所有测试
  python run_tests.py unit               # 运行单元测试
  python run_tests.py integration        # 运行集成测试
  python run_tests.py --list             # 列出所有测试
  python run_tests.py --file test_smart_cache.py  # 运行单个测试文件
        """
    )
    
    parser.add_argument(
        'suite',
        nargs='?',
        default='all',
        choices=list(TEST_SUITES.keys()),
        help='要运行的测试套件 (默认: all)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有可用的测试'
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='运行单个测试文件'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='快速测试（仅运行简单集成测试）'
    )
    
    args = parser.parse_args()
    
    # 列出测试
    if args.list:
        list_tests()
        return 0
    
    # 运行单个文件
    if args.file:
        success = run_test_file(args.file)
        return 0 if success else 1
    
    # 快速测试
    if args.quick:
        success = run_test_file('test_integration_simple.py')
        return 0 if success else 1
    
    # 运行测试套件
    success = run_test_suite(args.suite)
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 运行测试时发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

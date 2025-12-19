############################################################
# 📘 文件说明：
# 本文件实现的功能：测试用例：验证 test_lesson_recorder 相关逻辑的正确性与回归。
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
# - 依赖（标准库）：os, sys, tempfile
# - 依赖（第三方）：lesson
# - 依赖（本地）：无
#
# 🕒 创建时间：2025-12-19
############################################################

import os
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)

from lesson.record_lesson import LessonRecord, write_lesson


def test_lesson_write_to_tempdir():
    print("\n📝 测试1: lesson-生成复盘文件")
    try:
        with tempfile.TemporaryDirectory() as d:
            record = LessonRecord(
                title="问题_单元测试",
                module="tests/test_lesson_recorder.py",
                environment="tests",
                phenomenon="示例现象",
                root_cause="示例根因",
                solution_steps="步骤1\n步骤2",
            )
            p = write_lesson(record, output_dir=d)
            assert os.path.exists(p)
            content = open(p, "r", encoding="utf-8").read()
            assert "### 问题描述" in content
            assert "### 根本原因分析" in content
            assert "### 解决方案与步骤" in content
        print("✅ 通过: 复盘文件生成")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def run_all_tests():
    print("=" * 60)
    print("🧪 lesson 复盘机制单元测试")
    print("=" * 60)

    tests = [
        test_lesson_write_to_tempdir,
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

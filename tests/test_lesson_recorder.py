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

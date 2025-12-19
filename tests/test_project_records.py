import os
import sys
import json

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)


def _read(path: str) -> str:
    with open(os.path.join(REPO_ROOT, path), "r", encoding="utf-8") as f:
        return f.read()


def test_records_no_ascii_question_marks() -> bool:
    print("\n?? 测试: 项目记录文件无 ASCII 问号占位符")
    try:
        history_raw = _read("历史记录.json")
        progress_raw = _read("任务进度.json")

        # JSON 可解析
        json.loads(history_raw)
        json.loads(progress_raw)

        # 防止“编码替换写入”导致的 ?? 乱码
        assert "?" not in history_raw, "历史记录.json 含 ASCII '?'，疑似乱码占位符"
        assert "?" not in progress_raw, "任务进度.json 含 ASCII '?'，疑似乱码占位符"

        print("? 通过: 记录文件可解析且无 ASCII '?'")
        return True
    except Exception as e:
        print(f"? 失败: {e}")
        return False


def run_all_tests() -> bool:
    print("=" * 60)
    print("?? 项目记录文件回归测试")
    print("=" * 60)
    ok = test_records_no_ascii_question_marks()
    print("\n" + "=" * 60)
    print(f"?? 测试结果: {'通过' if ok else '失败'}")
    print("=" * 60)
    return ok


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

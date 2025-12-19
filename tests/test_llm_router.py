import os
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)
from core.orchestration.ai_router import LLMRouter


def test_router_fallback_echo():
    # Ensure the test is deterministic and does not depend on the developer
    # machine's environment variables (e.g. OPENAI_API_KEY).
    keys = [
        "OPENAI_API_KEY",
        "HEABL_OPENAI_KEY",
        "DEEPSEEK_API_KEY",
        "HEABL_DEEPSEEK_KEY",
        "ANTHROPIC_API_KEY",
        "GROQ_API_KEY",
        "HEABL_GROQ_KEY",
        "MOONSHOT_API_KEY",
        "HEABL_MOONSHOT_KEY",
        "GEMINI_API_KEY",
        "HEABL_GEMINI_KEY",
        "HEABL_DOUBAO_KEY",
        "HEABL_COOLYEAH_KEY",
        "ZHIPU_API_KEY",
        "HEABL_ZHIPU_KEY",
        "HEABL_LLM_PREFERENCE",
        "HEABL_LLM_DEFAULT",
        "AI_DEFAULT_PROVIDER",
    ]
    snapshot = {k: os.environ.get(k) for k in keys}
    try:
        for k in keys:
            os.environ.pop(k, None)
        os.environ["HEABL_LLM_PREFERENCE"] = "echo"
        router = LLMRouter()  # without keys will fall back to echo
        res = router.generate(prompt="ping", system="test", max_tokens=10)
        assert "content" in res
        assert res.get("provider") == "echo" or res.get("success") is False
    finally:
        for k, v in snapshot.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def run_all_tests() -> bool:
    print("=" * 60)
    print("🧪 LLM Router Tests")
    print("=" * 60)
    ok = True
    try:
        test_router_fallback_echo()
        print("[OK] test_router_fallback_echo")
    except Exception as e:
        ok = False
        print(f"[FAIL] test_router_fallback_echo: {type(e).__name__}: {e}")
        import traceback


        traceback.print_exc()
    print("=" * 60)
    print("PASS" if ok else "FAIL")
    print("=" * 60)
    return ok
if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)

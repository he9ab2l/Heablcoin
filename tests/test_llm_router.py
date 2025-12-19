import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)

from core.orchestration.ai_router import LLMRouter


def test_router_fallback_echo():
    router = LLMRouter()  # without keys will fall back to echo
    res = router.generate(prompt="ping", system="test", max_tokens=10)
    assert "content" in res
    assert res.get("provider") == "echo" or res.get("success") is False

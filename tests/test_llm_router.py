from orchestration.ai_router import LLMRouter


def test_router_fallback_echo():
    router = LLMRouter()  # without keys will fall back to echo
    res = router.generate(prompt="ping", system="test", max_tokens=10)
    assert "content" in res
    assert res.get("provider") == "echo" or res.get("success") is False

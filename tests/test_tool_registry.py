"""
Unit tests: MCP tool registry & soft-disable.
This test validates:
- `mcp_tool_safe` registers tools into `core.tool_registry`
- runtime override via `set_tool_enabled`
- env-based disable via `TOOLS_DISABLED`
"""
import os
import sys


# Add project path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, REPO_ROOT)


def test_tool_registry_and_soft_disable() -> bool:
    from core.mcp_safety import mcp_tool_safe
    from core.tool_registry import is_tool_enabled, list_tools, reset_tool_overrides, set_tool_enabled


    tool_name = "tool_registry_dummy_for_test"
    @mcp_tool_safe
    def tool_registry_dummy_for_test() -> str:  # noqa: F811 - same as tool_name
        raise RuntimeError("should not run when disabled")
    # Registered
    tools = list_tools()
    assert any(t.get("name") == tool_name for t in tools), "tool should be registered in tool_registry"
    assert is_tool_enabled(tool_name) is True, "tool should be enabled by default"
    # Runtime disable
    set_tool_enabled(tool_name, False)
    disabled_msg = tool_registry_dummy_for_test()
    assert "工具已禁用" in disabled_msg, "disabled tool should return a disabled message"
    reset_tool_overrides()
    # Env disable
    old = os.environ.get("TOOLS_DISABLED")
    os.environ["TOOLS_DISABLED"] = tool_name
    try:
        disabled_msg = tool_registry_dummy_for_test()
        assert "工具已禁用" in disabled_msg, "env-disabled tool should return a disabled message"
    finally:
        if old is None:
            os.environ.pop("TOOLS_DISABLED", None)
        else:
            os.environ["TOOLS_DISABLED"] = old
    return True


def run_all_tests() -> bool:
    print("=" * 60)
    print("Tool Registry Tests")
    print("=" * 60)
    ok = True
    try:
        ok = bool(test_tool_registry_and_soft_disable())
        print("[OK] test_tool_registry_and_soft_disable")
    except Exception as e:
        ok = False
        print(f"[FAIL] test_tool_registry_and_soft_disable: {type(e).__name__}: {e}")
        import traceback


        traceback.print_exc()
    print("=" * 60)
    print("PASS" if ok else "FAIL")
    print("=" * 60)
    return ok
if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)

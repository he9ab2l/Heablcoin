import argparse
import os
import subprocess
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
TEST_SUITES = {
    "unit": [
        "test_smart_logger.py",
        "test_smart_cache.py",
        "test_mcp_tools.py",
        "test_mcp_call_backups.py",
        "test_tool_registry.py",
        "test_visualization_output.py",
        "test_risk_management.py",
        "test_risk_extensions.py",
        "test_notifier.py",
        "test_backtesting.py",
        "test_exchange_adapter.py",
        "test_env_helpers.py",
        "test_llm_router.py",
        "test_project_records.py",
        "test_validators.py",
        "test_task_executor.py",
        "test_strategy_performance.py",
        "test_market_quality_modules.py",
        "test_governance_monitors.py",
        "test_feishu_push.py",
    ],
    "email": [
        "test_email_connection.py",
    ],
    "integration": [
        "test_integration_simple.py",
        "test_mcp_stdio_startup.py",
        "test_integration_full.py",
    ],
    "stress": [
        "test_stress_task_executor.py",
    ],
}
TEST_SUITES["all"] = TEST_SUITES["unit"] + TEST_SUITES["integration"]


def run_test_file(test_file: str) -> bool:
    path = os.path.join(os.path.dirname(__file__), test_file)
    if not os.path.exists(path):
        print(f"[WARN] missing test file: {test_file}")
        return False
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    extra_paths = [REPO_ROOT, SRC_DIR]
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(
        [p for p in extra_paths if p] + ([existing] if existing else [])
    )
    print("=" * 60)
    print(f"[RUN] {test_file}")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, path],
        cwd=REPO_ROOT,
        env=env,
        text=True,
    )
    if result.returncode == 0:
        print(f"[PASS] {test_file}")
        return True
    print(f"[FAIL] {test_file}")
    return False


def main():
    parser = argparse.ArgumentParser(description="Heablcoin test runner")
    parser.add_argument(
        "suite",
        nargs="?",
        default="all",
        choices=list(TEST_SUITES.keys()),
        help="unit/email/integration/stress/all",
    )
    parser.add_argument("--list", action="store_true", help="list available tests")
    parser.add_argument("--file", help="run a single test file")
    args = parser.parse_args()
    if args.list:
        for name, tests in TEST_SUITES.items():
            print(f"{name}:")
            for t in tests:
                print(f"  - {t}")
        return 0
    if args.file:
        return 0 if run_test_file(args.file) else 1
    suite_tests = TEST_SUITES.get(args.suite, [])
    failures = 0
    for test in suite_tests:
        if not run_test_file(test):
            failures += 1
    print("=" * 60)
    print(f"[SUMMARY] suite={args.suite} passed={len(suite_tests)-failures} failed={failures}")
    print("=" * 60)
    return 0 if failures == 0 else 1
if __name__ == "__main__":
    raise SystemExit(main())

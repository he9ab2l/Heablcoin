"""
单元测试：飞书推送（src/core/cloud/pipeline_worker.py）

目标：不发真实网络请求，通过 monkeypatch requests.post 验证：
1) 未配置 FEISHU_WEBHOOK 时返回友好错误
2) 配置 webhook 时可正常组装 payload 并判定 success
3) 配置 FEISHU_SECRET 时会带 timestamp/sign，且 sign 可校验
"""

from __future__ import annotations

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)

from core.cloud import pipeline_worker as pw


def test_notify_feishu_missing_webhook() -> bool:
    old_webhook = os.environ.pop("FEISHU_WEBHOOK", None)
    old_secret = os.environ.pop("FEISHU_SECRET", None)
    try:
        res = pw.notify_feishu("title", "text")
        assert res.get("success") is False
        assert "FEISHU_WEBHOOK" in (res.get("error") or "")
        return True
    finally:
        if old_webhook is not None:
            os.environ["FEISHU_WEBHOOK"] = old_webhook
        if old_secret is not None:
            os.environ["FEISHU_SECRET"] = old_secret


def test_notify_feishu_payload_without_secret() -> bool:
    old_webhook = os.environ.get("FEISHU_WEBHOOK")
    old_secret = os.environ.get("FEISHU_SECRET")
    os.environ["FEISHU_WEBHOOK"] = "https://example.com/webhook"
    os.environ["FEISHU_SECRET"] = ""

    calls = {}

    def fake_post(url, headers=None, data=None, timeout=None):
        calls["url"] = url
        calls["headers"] = headers or {}
        calls["data"] = data
        calls["timeout"] = timeout

        class Resp:
            status_code = 200
            text = "ok"

            def json(self):
                return {"StatusCode": 0}

        return Resp()

    orig = pw.requests.post
    pw.requests.post = fake_post
    try:
        res = pw.notify_feishu("hello", "world")
        assert res.get("success") is True
        payload = json.loads(calls["data"])
        assert payload.get("msg_type") == "text"
        assert "timestamp" not in payload
        assert "sign" not in payload
        assert "hello" in payload["content"]["text"]
        return True
    finally:
        pw.requests.post = orig
        if old_webhook is None:
            os.environ.pop("FEISHU_WEBHOOK", None)
        else:
            os.environ["FEISHU_WEBHOOK"] = old_webhook
        if old_secret is None:
            os.environ.pop("FEISHU_SECRET", None)
        else:
            os.environ["FEISHU_SECRET"] = old_secret


def test_notify_feishu_payload_with_secret() -> bool:
    old_webhook = os.environ.get("FEISHU_WEBHOOK")
    old_secret = os.environ.get("FEISHU_SECRET")
    os.environ["FEISHU_WEBHOOK"] = "https://example.com/webhook"
    os.environ["FEISHU_SECRET"] = "my_secret"

    calls = {}

    def fake_post(url, headers=None, data=None, timeout=None):
        calls["url"] = url
        calls["headers"] = headers or {}
        calls["data"] = data
        calls["timeout"] = timeout

        class Resp:
            status_code = 200
            text = "ok"

            def json(self):
                return {"StatusCode": 0}

        return Resp()

    orig = pw.requests.post
    pw.requests.post = fake_post
    try:
        res = pw.notify_feishu("hello", "world")
        assert res.get("success") is True
        payload = json.loads(calls["data"])
        assert payload.get("timestamp")
        assert payload.get("sign")
        # 校验签名可复算
        expected = pw._feishu_sign(os.environ["FEISHU_SECRET"], payload["timestamp"])
        assert payload["sign"] == expected
        return True
    finally:
        pw.requests.post = orig
        if old_webhook is None:
            os.environ.pop("FEISHU_WEBHOOK", None)
        else:
            os.environ["FEISHU_WEBHOOK"] = old_webhook
        if old_secret is None:
            os.environ.pop("FEISHU_SECRET", None)
        else:
            os.environ["FEISHU_SECRET"] = old_secret


def run_all_tests() -> bool:
    print("=" * 60)
    print("🧪 Feishu Push Tests")
    print("=" * 60)

    ok = True
    for fn in [
        test_notify_feishu_missing_webhook,
        test_notify_feishu_payload_without_secret,
        test_notify_feishu_payload_with_secret,
    ]:
        try:
            assert fn()
            print(f"[OK] {fn.__name__}")
        except Exception as e:
            ok = False
            print(f"[FAIL] {fn.__name__}: {type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()

    print("=" * 60)
    print("PASS" if ok else "FAIL")
    print("=" * 60)
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if run_all_tests() else 1)

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def learning_store_dir() -> Path:
    here = Path(__file__).resolve().parent.parent
    out = here / "reports" / "learning_sessions"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _session_path(session_id: str) -> Path:
    return learning_store_dir() / f"{session_id}.json"


def create_session(kind: str, prompt: str, payload: Dict[str, Any], answer_key: Dict[str, Any]) -> str:
    session_id = uuid.uuid4().hex
    created_at = datetime.now().isoformat()
    data = {
        "id": session_id,
        "kind": str(kind or "").strip() or "unknown",
        "created_at": created_at,
        "prompt": str(prompt or ""),
        "payload": payload or {},
        "answer_key": answer_key or {},
        "submissions": [],
    }
    _session_path(session_id).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return session_id


def load_session(session_id: str) -> Optional[Dict[str, Any]]:
    p = _session_path(session_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_session(session: Dict[str, Any]) -> bool:
    sid = str(session.get("id") or "").strip()
    if not sid:
        return False
    p = _session_path(sid)
    try:
        p.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        return True
    except Exception:
        return False


def append_submission(session_id: str, answer: str, result: Dict[str, Any]) -> bool:
    session = load_session(session_id)
    if not isinstance(session, dict):
        return False
    subs: List[Dict[str, Any]] = session.get("submissions") if isinstance(session.get("submissions"), list) else []
    subs.append({
        "at": datetime.now().isoformat(),
        "answer": str(answer or ""),
        "result": result or {},
    })
    session["submissions"] = subs
    return save_session(session)


def list_sessions(limit: int = 20) -> List[Dict[str, Any]]:
    lim = int(limit) if limit and int(limit) > 0 else 20
    base = learning_store_dir()
    items = sorted(base.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: List[Dict[str, Any]] = []
    for p in items[:lim]:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        out.append({
            "id": data.get("id"),
            "kind": data.get("kind"),
            "created_at": data.get("created_at"),
            "prompt": (data.get("prompt") or "")[:120],
            "submissions": len(data.get("submissions") or []),
        })
    return out


__all__ = [
    "learning_store_dir",
    "create_session",
    "load_session",
    "save_session",
    "append_submission",
    "list_sessions",
]

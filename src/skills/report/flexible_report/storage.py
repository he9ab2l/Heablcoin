from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, Optional

from .utils import safe_filename_component
from utils.project_paths import PROJECT_ROOT


def reports_base_dir() -> Path:
    return PROJECT_ROOT / "reports" / "flexible_report"


def save_backup(
    title: str,
    full_html: str,
    enabled_modules: Dict[str, bool],
    send_result: Dict[str, Any],
    resolved_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    created_at = datetime.now()
    date_str = created_at.strftime("%Y%m%d")
    ts_str = created_at.strftime("%Y%m%d_%H%M%S")
    safe_title = safe_filename_component(title)
    out_dir = reports_base_dir() / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    base = f"{ts_str}__{safe_title}"
    html_path = out_dir / f"{base}.html"
    meta_path = out_dir / f"{base}.meta.json"
    data_path = out_dir / f"{base}.data.json"

    html_path.write_text(str(full_html or ""), encoding="utf-8", newline="\n")
    if resolved_data is None:
        resolved_data = {}
    data_path.write_text(json.dumps(resolved_data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    meta = {
        "title": title,
        "created_at": created_at.isoformat(),
        "modules": {k: bool(v) for k, v in enabled_modules.items()},
        "paths": {"html": str(html_path), "meta": str(meta_path), "data": str(data_path)},
        "email": {"result": send_result},
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return {"html": str(html_path), "meta": str(meta_path), "data": str(data_path)}


__all__ = ["reports_base_dir", "save_backup"]

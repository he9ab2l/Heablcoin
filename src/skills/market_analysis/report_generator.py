from __future__ import annotations


import json

from typing import Any, Dict, List


def to_markdown(title: str, module_results: List[Dict[str, Any]]) -> str:

    parts: List[str] = []

    if title:

        parts.append(f"# {title}\n")

    for r in module_results:

        name = str(r.get("name") or "module")

        md = str(r.get("markdown") or "").strip()

        if not md:

            continue

        parts.append(f"\n## {name}\n\n")

        parts.append(md + "\n")

    return "".join(parts).strip() + "\n"


def to_json(title: str, module_results: List[Dict[str, Any]]) -> str:

    obj = {"title": title, "modules": module_results}

    return json.dumps(obj, ensure_ascii=False, indent=2)

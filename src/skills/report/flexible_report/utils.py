from __future__ import annotations


from datetime import datetime

import html

import os

import re

import socket

from typing import Any


def esc(v: Any) -> str:

    return html.escape("" if v is None else str(v), quote=True)


def fmt_money(v: Any, digits: int = 2) -> str:

    try:

        return f"{float(v):,.{digits}f}"

    except Exception:

        return esc(v)


def now_str() -> str:

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def server_id() -> str:

    return os.getenv("SERVER_ID") or socket.gethostname()


def env_bool(name: str, default: bool = True) -> bool:

    v = os.getenv(name)

    if v is None:

        return default

    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def re_sub_strip_html(body_html: str) -> str:

    raw = str(body_html or "")

    out = []

    in_tag = False

    for ch in raw:

        if ch == "<":

            in_tag = True

            continue

        if ch == ">":

            in_tag = False

            continue

        if not in_tag:

            out.append(ch)

    text = "".join(out)

    return " ".join(text.split()).strip()


def safe_filename_component(value: str) -> str:

    v = (value or "").strip()

    v = v.replace("/", "_").replace("\\", "_")

    v = re.sub(r"[^A-Za-z0-9._-]+", "_", v)

    v = re.sub(r"_+", "_", v).strip("_")

    return v or "unknown"


__all__ = [

    "env_bool",

    "esc",

    "fmt_money",

    "now_str",

    "re_sub_strip_html",

    "safe_filename_component",

    "server_id",

]

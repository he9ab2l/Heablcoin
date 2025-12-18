############################################################
# 📘 文件说明：报告服务
# 本文件实现的功能：报告生成的核心服务
#
# 📋 程序整体伪代码（中文）：
# 1. 初始化依赖模块和配置
# 2. 定义核心类和函数
# 3. 实现主要业务逻辑
# 4. 提供对外接口
# 5. 异常处理与日志记录
#
# 🔄 程序流程图（逻辑流）：
# ┌──────────────┐
# │  输入数据    │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  核心处理逻辑 │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  输出结果    │
# └──────────────┘
#
# 📊 数据管道说明：
# 数据流向：输入源 → 数据处理 → 核心算法 → 输出目标
#
# 🧩 文件结构：
# - 函数: notify_allowed, send_raw_html_smtp, coalesce_data, register_tools, send_flexible_report
#
# 🔗 主要依赖：__future__, email, json, os, report, smtplib, typing
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

import os
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
from typing import Any, Dict, List, Optional

from .defaults import (
    default_A,
    default_B,
    default_C,
    default_D,
    default_E,
    default_F,
    default_G,
    default_H,
)
from .render import EmailBuilder, render_base_email
from .state import set_data_providers, set_notify_switch_fn, set_send_email_fn, get_send_email_fn, get_notify_switch_fn
from .storage import save_backup
from .utils import env_bool, re_sub_strip_html


def notify_allowed(msg_type: str) -> bool:
    fn = get_notify_switch_fn()
    if fn is not None:
        try:
            return bool(fn(msg_type))
        except Exception:
            return True

    t = (msg_type or "").upper().strip()
    if t in {"REPORT", "DAILY_REPORT"}:
        return env_bool("NOTIFY_DAILY_REPORT", True)
    return True


def send_raw_html_smtp(subject: str, full_html: str) -> bool:
    if os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "False").lower() != "true":
        return False

    sender = os.getenv("SENDER_EMAIL")
    password = os.getenv("SENDER_PASSWORD")
    receiver = os.getenv("RECIPIENT_EMAIL") or os.getenv("RECEIVER_EMAIL") or os.getenv("NOTIFY_EMAIL")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.qq.com")
    try:
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
    except Exception:
        smtp_port = 465

    if not all([sender, password, receiver]):
        return False

    safe_subject = str(subject or "").strip() or "Heablcoin"

    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = str(Header(safe_subject, "utf-8"))

    plain_fallback = re_sub_strip_html(full_html) or safe_subject
    msg.attach(MIMEText(plain_fallback, "plain", "utf-8"))
    msg.attach(MIMEText(full_html, "html", "utf-8"))

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30) as server:
                server.login(sender, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)
        return True
    except Exception:
        return False


def coalesce_data(kwargs: Dict[str, Any], module_key: str, default: Dict[str, Any]) -> Dict[str, Any]:
    direct = kwargs.get(f"data_{module_key}")
    if isinstance(direct, dict):
        merged = dict(default)
        merged.update(direct)
        return merged

    pref = f"{module_key}_"
    merged = dict(default)
    for k, v in kwargs.items():
        if k.startswith(pref):
            merged[k[len(pref):]] = v
    return merged


def register_tools(
    mcp: Any,
    send_email_fn: Optional[Any] = None,
    notify_switch_fn: Optional[Any] = None,
    data_providers: Optional[Dict[str, Any]] = None,
) -> None:
    set_send_email_fn(send_email_fn)
    set_notify_switch_fn(notify_switch_fn)
    set_data_providers(data_providers)
    mcp.tool()(send_flexible_report)


def send_flexible_report(
    title: str = "综合报告",
    send_A: bool = False,
    send_B: bool = False,
    send_C: bool = False,
    send_D: bool = False,
    send_E: bool = False,
    send_F: bool = False,
    send_G: bool = False,
    send_H: bool = False,
    send_I: bool = False,
    **kwargs: Any,
) -> str:
    builder = EmailBuilder()

    enabled = {
        "A": bool(send_A),
        "B": bool(send_B),
        "C": bool(send_C),
        "D": bool(send_D),
        "E": bool(send_E),
        "F": bool(send_F),
        "G": bool(send_G),
        "H": bool(send_H),
        "I": bool(send_I),
    }

    if not any(enabled.values()):
        enabled = {k: True for k in enabled}

    parts: List[str] = []
    resolved_data: Dict[str, Any] = {}

    if enabled["A"]:
        data = coalesce_data(kwargs, "A", default_A())
        resolved_data["A"] = data
        parts.append(builder.render_A(data))

    if enabled["B"]:
        data = coalesce_data(kwargs, "B", default_B())
        resolved_data["B"] = data
        parts.append(builder.render_B(data))

    if enabled["C"]:
        data = coalesce_data(kwargs, "C", default_C(kwargs))
        resolved_data["C"] = data
        parts.append(builder.render_C(data))

    if enabled["D"]:
        data = coalesce_data(kwargs, "D", default_D(kwargs))
        resolved_data["D"] = data
        parts.append(builder.render_D(data))

    if enabled["E"]:
        data = coalesce_data(kwargs, "E", default_E(kwargs))
        resolved_data["E"] = data
        parts.append(builder.render_E(data))

    if enabled["F"]:
        data = coalesce_data(kwargs, "F", default_F())
        resolved_data["F"] = data
        parts.append(builder.render_F(data))

    if enabled["G"]:
        data = coalesce_data(kwargs, "G", default_G(kwargs))
        resolved_data["G"] = data
        parts.append(builder.render_G(data))

    if enabled["H"]:
        data = coalesce_data(kwargs, "H", default_H(kwargs))
        resolved_data["H"] = data
        parts.append(builder.render_H(data))

    if enabled["I"]:
        data = coalesce_data(kwargs, "I", {"url": "https://example.com/heablcoin", "label": "打开控制台"})
        resolved_data["I"] = data
        parts.append(builder.render_I(data))

    content_html = "".join(parts)
    full_html = render_base_email(title, content_html)

    if not notify_allowed("REPORT"):
        chosen = ",".join([k for k, v in enabled.items() if v])
        paths = save_backup(
            title,
            full_html,
            enabled,
            {"attempted": False, "skipped_by_switch": True, "ok": False, "fallback_used": False},
            resolved_data,
        )
        return_format = str(kwargs.get("return_format") or "text").lower().strip()
        if return_format == "json":
            return json.dumps({"title": title, "modules": enabled, "paths": paths, "sent": False}, ensure_ascii=False, indent=2)
        return f"⏭️ 已按通知开关跳过发送: {title} | 模块: {chosen} | 备份: {paths['html']}"

    send_result: Dict[str, Any] = {"attempted": True, "ok": False, "fallback_used": False}

    ok = False
    send_fn = get_send_email_fn()
    if send_fn is not None:
        try:
            ok = bool(send_fn(title, full_html, msg_type="REPORT"))
            send_result["fallback_used"] = True
            send_result["ok"] = bool(ok)
        except Exception:
            ok = False
            send_result["fallback_used"] = True
            send_result["ok"] = False
    else:
        ok = send_raw_html_smtp(title, full_html)
        send_result["ok"] = bool(ok)

    paths = save_backup(title, full_html, enabled, send_result, resolved_data)

    chosen = ",".join([k for k, v in enabled.items() if v])
    return_format = str(kwargs.get("return_format") or "text").lower().strip()
    if return_format == "json":
        return json.dumps({"title": title, "modules": enabled, "paths": paths, "sent": bool(ok)}, ensure_ascii=False, indent=2)
    if ok:
        return f"✅ 已发送: {title} | 模块: {chosen} | 备份: {paths['html']}"
    return f"❌ 发送失败或邮件通知未启用: {title} | 模块: {chosen} | 备份: {paths['html']} (请检查 .env: EMAIL_NOTIFICATIONS_ENABLED / SMTP 配置)"


__all__ = ["register_tools", "send_flexible_report"]

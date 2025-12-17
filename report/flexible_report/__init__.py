from __future__ import annotations

from report.flexible_report.analytics import compute_trade_analytics
from report.flexible_report.render import EmailBuilder, render_base_email
from report.flexible_report.service import register_tools, send_flexible_report
from report.flexible_report.utils import re_sub_strip_html

__all__ = [
    "EmailBuilder",
    "compute_trade_analytics",
    "render_base_email",
    "re_sub_strip_html",
    "register_tools",
    "send_flexible_report",
]

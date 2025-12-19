from __future__ import annotations


from .analytics import compute_trade_analytics

from .render import EmailBuilder, render_base_email

from .service import register_tools, send_flexible_report

from .utils import re_sub_strip_html


__all__ = [

    "EmailBuilder",

    "compute_trade_analytics",

    "render_base_email",

    "re_sub_strip_html",

    "register_tools",

    "send_flexible_report",

]

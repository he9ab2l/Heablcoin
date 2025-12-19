from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .trade_log import safe_float
from .utils import esc, fmt_money, now_str, server_id


def color_side(side: str) -> str:
    s = (side or "").upper().strip()
    if s == "BUY":
        return "#16a34a"
    if s == "SELL":
        return "#dc2626"
    return "#6b7280"


def label_side(side: str) -> str:
    s = (side or "").upper().strip() or "N/A"
    return s


def color_level(level: str) -> Dict[str, str]:
    lvl = (level or "").lower().strip()
    if lvl in {"high", "高"}:
        return {"bg": "#fde8e8", "border": "#dc2626", "text": "#991b1b"}
    if lvl in {"medium", "中", "mid"}:
        return {"bg": "#fff7e6", "border": "#f59e0b", "text": "#92400e"}
    return {"bg": "#eef2ff", "border": "#6366f1", "text": "#3730a3"}


def pill(text: str, color: str) -> str:
    return (
        f"<span style=\"display:inline-block;padding:2px 10px;border-radius:999px;"
        f"font-size:12px;line-height:18px;font-weight:700;background:{color};color:#ffffff;\">"
        f"{esc(text)}</span>"
    )


def progress_bar(percent: float, color: str) -> str:
    p = 0.0
    try:
        p = float(percent)
    except Exception:
        p = 0.0
    if p < 0:
        p = 0.0
    if p > 100:
        p = 100.0

    return (
        "<table role=\"presentation\" cellpadding=\"0\" cellspacing=\"0\" width=\"100%\" style=\"border-collapse:collapse;\">"
        "<tr>"
        "<td style=\"background:#e5e7eb;border-radius:999px;height:10px;overflow:hidden;\">"
        f"<table role=\"presentation\" cellpadding=\"0\" cellspacing=\"0\" width=\"{p:.0f}%\" style=\"border-collapse:collapse;\">"
        "<tr>"
        f"<td style=\"background:{color};height:10px;\"></td>"
        "</tr>"
        "</table>"
        "</td>"
        "</tr>"
        "</table>"
    )


def render_base_email(title: str, content_html: str) -> str:
    t = (title or "").strip() or "Heablcoin"
    created_at = now_str()
    sid = server_id()

    return (
        "<!doctype html>"
        "<html>"
        "<head>"
        "<meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{esc(t)}</title>"
        "</head>"
        "<body style=\"margin:0;padding:0;background:#f3f4f6;\">"
        "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;background:#f3f4f6;\">"
        "<tr>"
        "<td align=\"center\" style=\"padding:18px 12px;\">"
        "<table role=\"presentation\" width=\"600\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;width:100%;max-width:600px;\">"
        "<tr>"
        "<td style=\"padding:0 0 12px 0;\">"
        "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
        "<tr>"
        "<td style=\"font-family:Arial,'Segoe UI',sans-serif;font-size:18px;font-weight:800;color:#0f172a;\">Heablcoin</td>"
        f"<td align=\"right\" style=\"font-family:Arial,'Segoe UI',sans-serif;font-size:12px;color:#6b7280;\">{esc(created_at)}</td>"
        "</tr>"
        "</table>"
        "</td>"
        "</tr>"
        "<tr>"
        "<td style=\"padding:0 0 12px 0;\">"
        "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;background:#ffffff;border:1px solid #e5e7eb;border-radius:14px;\">"
        "<tr>"
        "<td style=\"padding:16px 18px;font-family:Arial,'Segoe UI',sans-serif;\">"
        "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
        "<tr>"
        f"<td style=\"font-size:20px;font-weight:800;color:#111827;\">{esc(t)}</td>"
        "</tr>"
        "<tr>"
        f"<td style=\"padding-top:6px;font-size:12px;color:#6b7280;\">Server: {esc(sid)}</td>"
        "</tr>"
        "</table>"
        "</td>"
        "</tr>"
        "</table>"
        "</td>"
        "</tr>"
        f"<tr><td style=\"padding:0;\">{content_html}</td></tr>"
        "<tr>"
        "<td style=\"padding:14px 4px 0 4px;font-family:Arial,'Segoe UI',sans-serif;font-size:12px;color:#9ca3af;line-height:1.6;\">"
        "本邮件由系统自动发送，请勿直接回复。若非本人操作，请立即检查账号与 API 权限。"
        "</td>"
        "</tr>"
        "</table>"
        "</td>"
        "</tr>"
        "</table>"
        "</body>"
        "</html>"
    )


class EmailBuilder:
    def __init__(self) -> None:
        self._font = "font-family:Arial,'Segoe UI',sans-serif;"

    def _spacer(self, h: int) -> str:
        hh = int(h) if isinstance(h, int) else 10
        if hh < 0:
            hh = 0
        return f"<tr><td height=\"{hh}\" style=\"font-size:0;line-height:0;\">&nbsp;</td></tr>"

    def _card(self, title: str, inner_html: str, accent_color: Optional[str] = None) -> str:
        accent = accent_color or "#e5e7eb"
        return (
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;margin:0 0 12px 0;\">"
            "<tr>"
            "<td style=\"padding:0;\">"
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;background:#ffffff;border:1px solid #e5e7eb;border-radius:14px;box-shadow:0 2px 10px rgba(15,23,42,0.06);\">"
            "<tr>"
            f"<td style=\"padding:0;border-top:6px solid {accent};border-radius:14px 14px 0 0;\">"
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
            "<tr>"
            f"<td style=\"padding:14px 16px 10px 16px;{self._font}font-size:14px;font-weight:800;color:#0f172a;\">{esc(title)}</td>"
            "</tr>"
            "<tr>"
            f"<td style=\"padding:0 16px 16px 16px;{self._font}font-size:13px;color:#111827;line-height:1.6;\">{inner_html}</td>"
            "</tr>"
            "</table>"
            "</td>"
            "</tr>"
            "</table>"
            "</td>"
            "</tr>"
            "</table>"
        )

    def _kv_table(self, rows: List[Dict[str, Any]]) -> str:
        trs = []
        for r in rows:
            key = esc(r.get("k"))
            val = r.get("v", "")
            v_html = val if isinstance(val, str) else esc(val)
            trs.append(
                "<tr>"
                f"<td width=\"38%\" style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:12px;color:#64748b;\">{key}</td>"
                f"<td style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:#0f172a;font-weight:700;\">{v_html}</td>"
                "</tr>"
            )
        return (
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;\">"
            + "".join(trs)
            + "</table>"
        )

    def render_section_a(self, data: Dict[str, Any]) -> str:
        side = label_side(data.get("side", ""))
        accent = color_side(side)
        cost_ccy = esc(data.get("cost_ccy", "USDT"))

        total_html = (
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
            f"<tr><td style=\"font-size:24px;font-weight:900;color:{accent};\">{fmt_money(data.get('cost', 0))} {cost_ccy}</td></tr>"
            "<tr><td style=\"padding-top:2px;font-size:12px;color:#6b7280;\">Total Cost</td></tr>"
            "</table>"
        )

        kv = self._kv_table(
            [
                {"k": "订单ID", "v": f"<span style=\"font-family:Consolas,monospace;font-size:12px;\">{esc(data.get('order_id'))}</span>"},
                {"k": "交易对", "v": f"<span style=\"color:#2563eb;\">{esc(data.get('symbol'))}</span>"},
                {"k": "方向", "v": f"<span style=\"color:{accent};font-weight:900;\">{esc(side)}</span>"},
                {"k": "成交价", "v": f"${fmt_money(data.get('price'))}"},
                {"k": "数量", "v": fmt_money(data.get("qty"), 6)},
                {"k": "时间", "v": esc(data.get("time") or now_str())},
            ]
        )

        inner = (
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
            f"<tr><td>{pill('TRADE', accent)}<span style=\"margin-left:10px;{self._font}font-size:12px;color:#6b7280;\">Execution Notice</span></td></tr>"
            f"{self._spacer(10)}"
            f"<tr><td>{kv}</td></tr>"
            f"{self._spacer(10)}"
            f"<tr><td>{total_html}</td></tr>"
            "</table>"
        )
        return self._card("A. 交易执行通知", inner, accent_color=accent)

    def render_section_b(self, data: Dict[str, Any]) -> str:
        holdings: List[Dict[str, Any]] = list(data.get("holdings") or [])

        rows = []
        for h in holdings[:5]:
            chg = h.get("change_pct", 0.0)
            try:
                chg_f = float(chg)
            except Exception:
                chg_f = 0.0
            chg_color = "#16a34a" if chg_f >= 0 else "#dc2626"
            rows.append(
                "<tr>"
                f"<td style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:#0f172a;font-weight:800;\">{esc(h.get('asset'))}</td>"
                f"<td align=\"right\" style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:#0f172a;\">{fmt_money(h.get('qty'), 6)}</td>"
                f"<td align=\"right\" style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:#0f172a;\">${fmt_money(h.get('value'))}</td>"
                f"<td align=\"right\" style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:12px;color:{chg_color};font-weight:800;\">{chg_f:+.2f}%</td>"
                "</tr>"
            )

        table_html = (
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;\">"
            "<tr>"
            f"<td style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">币种</td>"
            f"<td align=\"right\" style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">数量</td>"
            f"<td align=\"right\" style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">价值</td>"
            f"<td align=\"right\" style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">24h</td>"
            "</tr>"
            + "".join(rows)
            + "</table>"
        )

        total = fmt_money(data.get("total_equity"))
        available = fmt_money(data.get("available_usdt"))

        inner = (
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
            f"<tr><td style=\"{self._font}font-size:12px;color:#6b7280;\">可用 USDT：<span style=\"font-weight:900;color:#0f172a;\">{available}</span></td></tr>"
            f"{self._spacer(10)}"
            f"<tr><td>{table_html}</td></tr>"
            f"{self._spacer(12)}"
            f"<tr><td style=\"font-size:24px;font-weight:900;color:#111827;\">${total}</td></tr>"
            "<tr><td style=\"padding-top:2px;font-size:12px;color:#6b7280;\">Total Equity</td></tr>"
            "</table>"
        )
        return self._card("B. 账户资产快照", inner, accent_color="#2563eb")

    def render_section_c(self, data: Dict[str, Any]) -> str:
        action = (data.get("advice") or "观望").upper().strip()
        action_color = "#16a34a" if action in {"BUY", "买入"} else ("#dc2626" if action in {"SELL", "卖出"} else "#64748b")

        try:
            conf = float(data.get("confidence", 0))
        except Exception:
            conf = 0.0
        if conf < 0:
            conf = 0.0
        if conf > 100:
            conf = 100.0

        stars = int(round(conf / 20.0))
        star_text = "".join(["★" if i < stars else "☆" for i in range(5)])

        kv = self._kv_table(
            [
                {"k": "建议操作", "v": f"<span style=\"color:{action_color};font-weight:900;\">{esc(action)}</span>"},
                {"k": "信心指数", "v": f"<span style=\"font-weight:900;\">{conf:.0f}%</span> <span style=\"color:#f59e0b;\">{esc(star_text)}</span>"},
                {"k": "RSI", "v": esc(data.get("rsi"))},
                {"k": "MACD", "v": esc(data.get("macd"))},
                {"k": "支撑位", "v": esc(data.get("support"))},
                {"k": "阻力位", "v": esc(data.get("resistance"))},
            ]
        )

        inner = (
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
            f"<tr><td>{pill('AI', '#0ea5e9')}<span style=\"margin-left:8px;{self._font}font-size:12px;color:#6b7280;\">Decision Summary</span></td></tr>"
            f"{self._spacer(10)}"
            f"<tr><td>{kv}</td></tr>"
            "</table>"
        )
        return self._card("C. AI 交易决策", inner, accent_color=action_color)

    def render_section_d(self, data: Dict[str, Any]) -> str:
        pnl = 0.0
        try:
            pnl = float(data.get("pnl", 0))
        except Exception:
            pnl = 0.0
        pnl_color = "#16a34a" if pnl >= 0 else "#dc2626"

        pnl_pct = 0.0
        try:
            pnl_pct = float(data.get("pnl_pct", 0))
        except Exception:
            pnl_pct = 0.0

        win_rate = 0.0
        try:
            win_rate = float(data.get("win_rate", 0))
        except Exception:
            win_rate = 0.0

        max_dd = 0.0
        try:
            max_dd = float(data.get("max_drawdown", 0))
        except Exception:
            max_dd = 0.0

        roi_pct = 0.0
        try:
            roi_pct = float(data.get("roi_pct", 0))
        except Exception:
            roi_pct = 0.0

        sharpe = 0.0
        try:
            sharpe = float(data.get("sharpe", 0))
        except Exception:
            sharpe = 0.0

        profit_factor = data.get("profit_factor")
        rr_ratio = data.get("rr_ratio")
        avg_holding_s = int(safe_float(data.get("avg_holding_seconds"), 0.0))

        def fmt_pf(v: Any) -> str:
            try:
                fv = float(v)
                if math.isinf(fv):
                    return "∞"
                return f"{fv:.2f}"
            except Exception:
                return esc(v)

        holding_txt = "-"
        if avg_holding_s > 0:
            hrs = avg_holding_s // 3600
            mins = (avg_holding_s % 3600) // 60
            holding_txt = f"{hrs}h {mins}m" if hrs else f"{mins}m"

        big = (
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
            f"<tr><td style=\"font-size:28px;font-weight:900;color:{pnl_color};\">{pnl:+,.2f} USDT</td></tr>"
            f"<tr><td style=\"padding-top:2px;font-size:12px;color:#6b7280;\">PnL {pnl_pct:+.2f}%</td></tr>"
            "</table>"
        )

        kv = self._kv_table(
            [
                {"k": "总投资回报率 (ROI)", "v": f"<span style=\"font-weight:900;\">{roi_pct:+.2f}%</span>"},
                {"k": "最大回撤 (MDD)", "v": f"<span style=\"color:#dc2626;font-weight:900;\">{max_dd:.2f}%</span>"},
                {"k": "胜率 (Win Rate)", "v": f"<span style=\"font-weight:900;\">{win_rate:.0f}%</span>"},
                {"k": "夏普比率 (Sharpe)", "v": f"<span style=\"font-weight:900;\">{sharpe:.2f}</span>"},
                {"k": "盈利因子 (Profit Factor)", "v": f"<span style=\"font-weight:900;\">{fmt_pf(profit_factor)}</span>"},
                {"k": "盈亏比 (R/R Ratio)", "v": f"<span style=\"font-weight:900;\">{fmt_pf(rr_ratio)}</span>"},
                {"k": "平均持仓时间", "v": f"<span style=\"font-weight:900;\">{esc(holding_txt)}</span>"},
            ]
        )

        bar = progress_bar(win_rate, "#16a34a")

        attribution = list(data.get("attribution") or [])
        attr_rows = []
        for it in attribution[:5]:
            sym = esc(it.get("symbol"))
            pnl_v = safe_float(it.get("pnl"), 0.0)
            pnl_c = "#16a34a" if pnl_v >= 0 else "#dc2626"
            wr = safe_float(it.get("win_rate"), 0.0)
            attr_rows.append(
                "<tr>"
                f"<td style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:#0f172a;font-weight:900;\">{sym}</td>"
                f"<td align=\"right\" style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:{pnl_c};font-weight:900;\">{pnl_v:+,.2f}</td>"
                f"<td align=\"right\" style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:12px;color:#334155;font-weight:800;\">{wr:.0f}%</td>"
                "</tr>"
            )

        attr_table = ""
        if attr_rows:
            attr_table = (
                "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;\">"
                "<tr>"
                f"<td style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">交易对</td>"
                f"<td align=\"right\" style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">PnL</td>"
                f"<td align=\"right\" style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">胜率</td>"
                "</tr>"
                + "".join(attr_rows)
                + "</table>"
            )

        review_items = list(data.get("review") or [])
        review_html = ""
        if review_items:
            review_html = "".join([f"<tr><td style=\"padding:4px 0;{self._font}font-size:12px;color:#334155;\">- {esc(x)}</td></tr>" for x in review_items[:8]])
            review_html = f"<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">{review_html}</table>"

        inner_rows = [
            f"<tr><td>{big}</td></tr>",
            self._spacer(12),
            f"<tr><td>{kv}</td></tr>",
            self._spacer(12),
            f"<tr><td style=\"{self._font}font-size:12px;color:#6b7280;\">胜率进度</td></tr>",
            self._spacer(6),
            f"<tr><td>{bar}</td></tr>",
        ]
        if attr_table:
            inner_rows.append(self._spacer(14))
            inner_rows.append(f"<tr><td style=\"{self._font}font-size:12px;color:#6b7280;font-weight:900;\">盈亏归因 (Top)</td></tr>")
            inner_rows.append(self._spacer(8))
            inner_rows.append(f"<tr><td>{attr_table}</td></tr>")
        if review_html:
            inner_rows.append(self._spacer(14))
            inner_rows.append(f"<tr><td style=\"{self._font}font-size:12px;color:#6b7280;font-weight:900;\">回溯测试审查</td></tr>")
            inner_rows.append(self._spacer(6))
            inner_rows.append(f"<tr><td>{review_html}</td></tr>")

        inner = "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">" + "".join(inner_rows) + "</table>"

        return self._card("D. 绩效复盘 (PnL)", inner, accent_color=pnl_color)

    def render_section_e(self, data: Dict[str, Any]) -> str:
        level = data.get("level", "中")
        palette = color_level(str(level))
        reasons = list(data.get("reasons") or [])
        action = data.get("action") or "请检查风控阈值、API 配置与仓位风险。"

        items = "".join([f"<tr><td style=\"padding:6px 0;{self._font}font-size:13px;color:{palette['text']};\">- {esc(r)}</td></tr>" for r in reasons])

        inner = (
            f"<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;background:{palette['bg']};border:1px solid #e5e7eb;border-left:6px solid {palette['border']};border-radius:12px;\">"
            "<tr>"
            f"<td style=\"padding:12px 14px;{self._font}\">"
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
            f"<tr><td style=\"font-size:14px;font-weight:900;color:{palette['text']};\">风险级别：{esc(level)}</td></tr>"
            f"<tr><td height=\"6\" style=\"font-size:0;line-height:0;\">&nbsp;</td></tr>"
            f"<tr><td><table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">{items}</table></td></tr>"
            f"<tr><td height=\"10\" style=\"font-size:0;line-height:0;\">&nbsp;</td></tr>"
            f"<tr><td style=\"font-size:12px;color:{palette['text']};\">建议：{esc(action)}</td></tr>"
            "</table>"
            "</td>"
            "</tr>"
            "</table>"
        )

        return self._card("E. 风险与安全警报", inner, accent_color=palette["border"])

    def render_section_f(self, data: Dict[str, Any]) -> str:
        trades: List[Dict[str, Any]] = list(data.get("trades") or [])
        rows = []
        for t in trades[:5]:
            side = label_side(t.get("side", ""))
            c = color_side(side)
            qty = t.get("qty")
            price = t.get("price")
            cost = t.get("cost")
            rows.append(
                "<tr>"
                f"<td style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:12px;color:#64748b;\">{esc(t.get('time'))}</td>"
                f"<td style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:#0f172a;font-weight:800;\">{esc(t.get('symbol'))}</td>"
                f"<td style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:{c};font-weight:900;\">{esc(side)}</td>"
                f"<td align=\"right\" style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:#0f172a;\">{fmt_money(qty, 6)}</td>"
                f"<td align=\"right\" style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:#0f172a;\">${fmt_money(price)}</td>"
                f"<td align=\"right\" style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:#0f172a;\">${fmt_money(cost)}</td>"
                "</tr>"
            )

        table_html = (
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;\">"
            "<tr>"
            f"<td style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">时间</td>"
            f"<td style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">交易对</td>"
            f"<td style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">方向</td>"
            f"<td align=\"right\" style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">数量</td>"
            f"<td align=\"right\" style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">价格</td>"
            f"<td align=\"right\" style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">成交额</td>"
            "</tr>"
            + "".join(rows)
            + "</table>"
        )

        return self._card("F. 最近交易历史", table_html, accent_color="#0ea5e9")

    def render_section_g(self, data: Dict[str, Any]) -> str:
        try:
            fg = float(data.get("fear_greed", 50))
        except Exception:
            fg = 50.0
        if fg < 0:
            fg = 0.0
        if fg > 100:
            fg = 100.0

        label = data.get("label") or ("恐慌" if fg < 40 else ("贪婪" if fg > 60 else "中性"))
        trend = data.get("trend") or "震荡"

        bar_color = "#16a34a" if fg > 60 else ("#f59e0b" if fg >= 40 else "#dc2626")

        left = (
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
            f"<tr><td style=\"font-size:22px;font-weight:900;color:#111827;\">{fg:.0f}</td></tr>"
            f"<tr><td style=\"padding-top:2px;font-size:12px;color:#6b7280;\">情绪指数：{esc(label)}</td></tr>"
            f"<tr><td height=\"10\" style=\"font-size:0;line-height:0;\">&nbsp;</td></tr>"
            f"<tr><td>{progress_bar(fg, bar_color)}</td></tr>"
            f"<tr><td height=\"10\" style=\"font-size:0;line-height:0;\">&nbsp;</td></tr>"
            f"<tr><td style=\"font-size:12px;color:#6b7280;\">大盘趋势：<span style=\"font-weight:900;color:#0f172a;\">{esc(trend)}</span></td></tr>"
            "</table>"
        )

        gainers = list(data.get("top_gainers") or [])
        losers = list(data.get("top_losers") or [])

        def movers(title: str, items: List[Dict[str, Any]], is_up: bool) -> str:
            rws = []
            for it in items[:3]:
                pct = 0.0
                try:
                    pct = float(it.get("pct", 0))
                except Exception:
                    pct = 0.0
                c = "#16a34a" if is_up else "#dc2626"
                rws.append(
                    "<tr>"
                    f"<td style=\"padding:6px 0;{self._font}font-size:13px;color:#0f172a;font-weight:800;\">{esc(it.get('symbol'))}</td>"
                    f"<td align=\"right\" style=\"padding:6px 0;{self._font}font-size:12px;color:{c};font-weight:900;\">{pct:+.2f}%</td>"
                    "</tr>"
                )

            return (
                "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
                f"<tr><td style=\"font-size:12px;color:#6b7280;font-weight:900;\">{esc(title)}</td></tr>"
                "<tr><td height=\"6\" style=\"font-size:0;line-height:0;\">&nbsp;</td></tr>"
                "<tr><td>"
                "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
                + "".join(rws)
                + "</table>"
                "</td></tr>"
                "</table>"
            )

        right = (
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;border:1px solid #e5e7eb;border-radius:12px;\">"
            "<tr>"
            f"<td style=\"padding:12px 12px;{self._font}\">"
            f"{movers('Top 3 涨幅', gainers, True)}"
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\"><tr><td height=\"10\" style=\"font-size:0;line-height:0;\">&nbsp;</td></tr></table>"
            f"{movers('Top 3 跌幅', losers, False)}"
            "</td>"
            "</tr>"
            "</table>"
        )

        inner = (
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
            "<tr>"
            f"<td width=\"44%\" valign=\"top\" style=\"padding:0 10px 0 0;{self._font}\">{left}</td>"
            f"<td valign=\"top\" style=\"padding:0;{self._font}\">{right}</td>"
            "</tr>"
            "</table>"
        )

        return self._card("G. 市场情绪概览", inner, accent_color=bar_color)

    def render_section_h(self, data: Dict[str, Any]) -> str:
        orders: List[Dict[str, Any]] = list(data.get("orders") or [])

        rows = []
        for o in orders:
            side = label_side(o.get("side", ""))
            c = color_side(side)
            dist = 0.0
            try:
                dist = float(o.get("distance_pct", 0))
            except Exception:
                dist = 0.0
            dist_color = "#dc2626" if abs(dist) < 0.5 else ("#f59e0b" if abs(dist) < 1.5 else "#16a34a")

            rows.append(
                "<tr>"
                f"<td style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:#0f172a;font-weight:800;\">{esc(o.get('symbol'))}</td>"
                f"<td style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:{c};font-weight:900;\">{esc(side)}</td>"
                f"<td align=\"right\" style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:#0f172a;\">${fmt_money(o.get('price'))}</td>"
                f"<td align=\"right\" style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:13px;color:#0f172a;\">{fmt_money(o.get('qty'), 6)}</td>"
                f"<td align=\"right\" style=\"padding:8px 10px;border-bottom:1px solid #f1f5f9;{self._font}font-size:12px;color:{dist_color};font-weight:900;\">{dist:+.2f}%</td>"
                "</tr>"
            )

        table_html = (
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;\">"
            "<tr>"
            f"<td style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">交易对</td>"
            f"<td style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">方向</td>"
            f"<td align=\"right\" style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">价格</td>"
            f"<td align=\"right\" style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">数量</td>"
            f"<td align=\"right\" style=\"padding:8px 10px;background:#f8fafc;{self._font}font-size:12px;color:#64748b;font-weight:800;\">距现价</td>"
            "</tr>"
            + "".join(rows)
            + "</table>"
        )

        return self._card("H. 当前挂单状态", table_html, accent_color="#8b5cf6")

    def render_section_i(self, data: Dict[str, Any]) -> str:
        url = (data.get("url") or "https://example.com").strip()
        label = (data.get("label") or "打开 Heablcoin 面板").strip()

        button = (
            "<table role=\"presentation\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
            "<tr>"
            "<td bgcolor=\"#2563eb\" style=\"border-radius:10px;\">"
            f"<a href=\"{esc(url)}\" style=\"display:inline-block;padding:12px 18px;{self._font}font-size:14px;color:#ffffff;text-decoration:none;font-weight:900;\">{esc(label)}</a>"
            "</td>"
            "</tr>"
            "</table>"
        )

        inner = (
            "<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse:collapse;\">"
            f"<tr><td style=\"{self._font}font-size:13px;color:#334155;\">建议你登录平台查看详情、调整策略或修改通知设置。</td></tr>"
            f"{self._spacer(12)}"
            f"<tr><td>{button}</td></tr>"
            f"{self._spacer(10)}"
            f"<tr><td style=\"{self._font}font-size:12px;color:#6b7280;\">如果按钮无法点击，请复制链接打开：<br><span style=\"color:#2563eb;\">{esc(url)}</span></td></tr>"
            "</table>"
        )

        return self._card("I. 用户互动 / CTA", inner, accent_color="#2563eb")


__all__ = ["EmailBuilder", "render_base_email"]

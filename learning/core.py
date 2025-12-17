from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from learning.storage import create_session, load_session, append_submission
from market_analysis.data_provider import DataProvider
from market_analysis.modules.market_structure import analyze_structure


def _env_str(name: str, default: str) -> str:
    import os

    v = os.getenv(name)
    if v is None:
        return default
    v = v.strip()
    return v if v else default


def _parse_symbols(value: str) -> List[str]:
    parts = [p.strip() for p in (value or "").split(",") if p.strip()]
    return parts


def get_default_symbols() -> List[str]:
    default = _env_str(
        "ALLOWED_SYMBOLS",
        "BTC/USDT,ETH/USDT,BNB/USDT,ADA/USDT,XRP/USDT,SOL/USDT,DOT/USDT,DOGE/USDT,AVAX/USDT,LINK/USDT,MATIC/USDT,UNI/USDT,ATOM/USDT,LTC/USDT,ETC/USDT",
    )
    return _parse_symbols(default)


def _pct(a: float, b: float) -> float:
    if a == 0:
        return 0.0
    return (b - a) / a * 100.0


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


class LearningEngine:
    def __init__(self, provider: Optional[DataProvider] = None) -> None:
        self.provider = provider or DataProvider.instance()

    def create_scan_session(
        self,
        timeframe: str = "1h",
        symbols: str = "",
        candidates: int = 10,
        pick: int = 3,
        lookback: int = 24,
    ) -> Dict[str, Any]:
        sym_list = _parse_symbols(symbols) if symbols else get_default_symbols()
        cand = int(candidates) if candidates and int(candidates) > 0 else 10
        cand = min(max(cand, 5), 30)
        pick_n = int(pick) if pick and int(pick) > 0 else 3
        pick_n = min(max(pick_n, 1), 8)
        lb = int(lookback) if lookback and int(lookback) > 0 else 24
        lb = min(max(lb, 10), 200)

        sym_list = sym_list[:cand]
        rows: List[Dict[str, Any]] = []
        for s in sym_list:
            try:
                std = self.provider.get_standard_data(symbol=s, timeframe=timeframe, limit=max(lb, 50), include_ticker=False)
                df = std.df
                if df is None or len(df) < lb + 1:
                    continue
                close0 = _safe_float(df.iloc[-lb]["close"], 0.0)
                close1 = _safe_float(df.iloc[-1]["close"], 0.0)
                vol0 = _safe_float(df.iloc[-lb]["volume"], 0.0)
                vol1 = _safe_float(df.iloc[-1]["volume"], 0.0)
                price_chg = _pct(close0, close1)
                vol_chg = _pct(vol0, vol1) if vol0 > 0 else 0.0
                divergence = 1 if price_chg * vol_chg < 0 else 0
                strength = abs(price_chg) + abs(vol_chg) * 0.5
                rows.append({
                    "symbol": s,
                    "price_change_pct": round(price_chg, 2),
                    "volume_change_pct": round(vol_chg, 2),
                    "divergence": divergence,
                    "strength": round(strength, 2),
                })
            except Exception:
                continue

        rows.sort(key=lambda r: (r.get("divergence", 0), r.get("strength", 0)), reverse=True)
        answer = [r.get("symbol") for r in rows if r.get("divergence")][:pick_n]
        if len(answer) < pick_n:
            answer = [r.get("symbol") for r in rows][:pick_n]

        prompt = (
            f"# 市场扫描训练\n\n"
            f"我从候选列表里挑出了 {len(rows)} 个交易对（周期 {timeframe}）。\n"
            f"请你从下方数据中找出最符合‘量价不一致’特征的 {pick_n} 个交易对，并回复交易对列表（用逗号分隔）。\n\n"
            f"示例：BTC/USDT,ETH/USDT\n"
        )

        payload = {"timeframe": timeframe, "candidates": rows, "pick": pick_n}
        answer_key = {"answers": answer, "pick": pick_n}

        session_id = create_session(kind="scan", prompt=prompt, payload=payload, answer_key=answer_key)
        return {"session_id": session_id, "prompt": prompt, "payload": payload}

    def create_price_action_session(self, symbol: str = "BTC/USDT", timeframe: str = "1h", limit: int = 120) -> Dict[str, Any]:
        lim = int(limit) if limit and int(limit) > 0 else 120
        lim = min(max(lim, 80), 300)

        std = self.provider.get_standard_data(symbol=symbol, timeframe=timeframe, limit=lim, include_ticker=False)
        candles = []
        for row in std.ohlcv:
            if not isinstance(row, list) or len(row) < 6:
                continue
            candles.append({
                "timestamp": int(row[0]),
                "open": _safe_float(row[1]),
                "high": _safe_float(row[2]),
                "low": _safe_float(row[3]),
                "close": _safe_float(row[4]),
                "volume": _safe_float(row[5]),
            })

        structure = analyze_structure(std, {})
        payload_struct = structure.get("payload") if isinstance(structure, dict) else {}
        supports = payload_struct.get("support_levels") if isinstance(payload_struct, dict) else []
        resistances = payload_struct.get("resistance_levels") if isinstance(payload_struct, dict) else []
        key_levels = payload_struct.get("key_levels") if isinstance(payload_struct, dict) else []

        prompt = (
            f"# 价格行为训练\n\n"
            f"你将得到 {symbol} 的裸K数据（周期 {timeframe}）。\n"
            f"请你用自然语言或数字回答你认为的关键支撑/阻力位。\n"
            f"建议给出 2-4 个价格（例如：92000, 90500, 98000）。\n\n"
            f"提交答案请用 `submit_learning_answer`。\n"
        )

        payload = {
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": candles,
        }
        answer_key = {
            "support_levels": supports,
            "resistance_levels": resistances,
            "key_levels": key_levels,
        }

        session_id = create_session(kind="price_action", prompt=prompt, payload=payload, answer_key=answer_key)
        return {"session_id": session_id, "prompt": prompt, "payload": payload}

    def score_session(self, session_id: str, answer: str) -> str:
        session = load_session(session_id)
        if not isinstance(session, dict):
            return "❌ 未找到训练会话"

        kind = str(session.get("kind") or "")
        key = session.get("answer_key") if isinstance(session.get("answer_key"), dict) else {}

        if kind == "scan":
            return self._score_scan(session_id, answer, key)
        if kind == "price_action":
            return self._score_price_action(session_id, answer, key)
        return "❌ 不支持的训练类型"

    def _score_scan(self, session_id: str, answer: str, key: Dict[str, Any]) -> str:
        raw = str(answer or "")
        picks = [p.strip().upper() for p in raw.split(",") if p.strip()]
        answers = [str(s or "").upper() for s in (key.get("answers") or [])]
        answers_set = set(answers)
        picks_set = set(picks)

        hit = sorted(list(picks_set.intersection(answers_set)))
        miss = sorted(list(answers_set.difference(picks_set)))
        wrong = sorted(list(picks_set.difference(answers_set)))

        score = 0
        if answers:
            score = int(round(len(hit) / len(answers) * 100))

        result = {
            "score": score,
            "hit": hit,
            "miss": miss,
            "wrong": wrong,
            "answers": answers,
        }
        append_submission(session_id, raw, result)

        hit_md = "\n".join([f"- {s}" for s in hit]) if hit else "- 无"
        miss_md = "\n".join([f"- {s}" for s in miss]) if miss else "- 无"
        wrong_md = "\n".join([f"- {s}" for s in wrong]) if wrong else "- 无"

        return (
            f"# 训练评分（市场扫描）\n\n"
            f"**得分**: {score}/100\n\n"
            f"## 命中\n{hit_md}\n\n"
            f"## 漏选\n{miss_md}\n\n"
            f"## 误选\n{wrong_md}\n\n"
            f"## 复盘建议\n"
            f"- 先看价格趋势，再看成交量是否同步放大。\n"
            f"- 价格上涨但成交量持续下降，往往代表动能不足。\n"
        )

    def _score_price_action(self, session_id: str, answer: str, key: Dict[str, Any]) -> str:
        raw = str(answer or "")
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", raw)]
        nums = nums[:10]

        supports = key.get("support_levels") if isinstance(key.get("support_levels"), list) else []
        resistances = key.get("resistance_levels") if isinstance(key.get("resistance_levels"), list) else []

        target_levels: List[float] = []
        for r in supports:
            if isinstance(r, dict) and r.get("price") is not None:
                target_levels.append(_safe_float(r.get("price"), 0.0))
        for r in resistances:
            if isinstance(r, dict) and r.get("price") is not None:
                target_levels.append(_safe_float(r.get("price"), 0.0))

        target_levels = [x for x in target_levels if x > 0]
        target_levels = sorted(target_levels)

        tol = 0.8
        hit = 0
        matched: List[Dict[str, Any]] = []
        for n in nums:
            best = None
            best_pct = None
            for t in target_levels:
                pct = abs(n - t) / t * 100.0
                if best_pct is None or pct < best_pct:
                    best_pct = pct
                    best = t
            if best is not None and best_pct is not None and best_pct <= tol:
                hit += 1
                matched.append({"guess": n, "matched": best, "diff_pct": round(best_pct, 2)})

        score = 0
        if target_levels:
            score = min(100, int(round(hit / min(len(target_levels), 4) * 100)))

        result = {
            "score": score,
            "guesses": nums,
            "matched": matched,
            "support_levels": supports,
            "resistance_levels": resistances,
        }
        append_submission(session_id, raw, result)

        matched_md = "\n".join([f"- guess={m['guess']:.2f} -> {m['matched']:.2f} (diff {m['diff_pct']}%)" for m in matched]) if matched else "- 无"
        supports_md = "\n".join([f"- {r.get('price'):.2f}" for r in supports if isinstance(r, dict) and r.get('price') is not None]) if supports else "- 无"
        resist_md = "\n".join([f"- {r.get('price'):.2f}" for r in resistances if isinstance(r, dict) and r.get('price') is not None]) if resistances else "- 无"

        return (
            f"# 训练评分（价格行为）\n\n"
            f"**得分**: {score}/100\n\n"
            f"## 你的答案\n- {raw}\n\n"
            f"## 命中情况\n{matched_md}\n\n"
            f"## 参考支撑位\n{supports_md}\n\n"
            f"## 参考阻力位\n{resist_md}\n\n"
            f"## 复盘建议\n"
            f"- 优先找摆动高点/低点，再结合整数关口验证。\n"
            f"- 支撑/阻力不是一个点，而是一个区域。\n"
        )


__all__ = ["LearningEngine", "get_default_symbols"]

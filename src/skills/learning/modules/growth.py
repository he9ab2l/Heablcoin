############################################################
# 📘 文件说明：
# 本文件实现的功能：第四板块：成长与画像
#
# 📋 程序整体伪代码（中文）：
# 1. 初始化主要依赖与变量
# 2. 加载输入数据或接收外部请求
# 3. 执行主要逻辑步骤（如计算、处理、训练、渲染等）
# 4. 输出或返回结果
# 5. 异常处理与资源释放
#
# 🔄 程序流程图（逻辑流）：
# ┌──────────┐
# │  输入数据 │
# └─────┬────┘
#       ↓
# ┌────────────┐
# │  核心处理逻辑 │
# └─────┬──────┘
#       ↓
# ┌──────────┐
# │  输出结果 │
# └──────────┘
#
# 📊 数据管道说明：
# 数据流向：输入源 → 数据清洗/转换 → 核心算法模块 → 输出目标（文件 / 接口 / 终端）
#
# 🧩 文件结构：
# - 依赖（标准库）：__future__, datetime, json, os, pathlib, typing
# - 依赖（第三方）：无
# - 依赖（本地）：utils.smart_logger
#
# 🕒 创建时间：2025-12-19
############################################################

"""第四板块：成长与画像"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.smart_logger import get_logger


logger = get_logger('learning')


PROFILE_DIR = Path("reports/trader_profile")


def _ensure_dir() -> None:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)


class GrowthProfileModule:
    """成长与画像模块"""

    # 等级定义
    LEVELS = [
        {"level": 1, "title": "新手学徒", "min_score": 0},
        {"level": 2, "title": "初级交易员", "min_score": 100},
        {"level": 3, "title": "中级交易员", "min_score": 300},
        {"level": 4, "title": "高级交易员", "min_score": 600},
        {"level": 5, "title": "资深交易员", "min_score": 1000},
        {"level": 6, "title": "精英交易员", "min_score": 1500},
        {"level": 7, "title": "大师交易员", "min_score": 2500},
        {"level": 8, "title": "传奇交易员", "min_score": 5000},
    ]

    # 成就定义
    ACHIEVEMENTS = {
        "first_trade": {"name": "初出茅庐", "description": "完成第一笔交易", "points": 10},
        "first_win": {"name": "初尝胜果", "description": "第一次盈利", "points": 10},
        "win_streak_3": {"name": "连胜新星", "description": "连续3次盈利", "points": 30},
        "win_streak_5": {"name": "连胜高手", "description": "连续5次盈利", "points": 50},
        "win_streak_10": {"name": "连胜大师", "description": "连续10次盈利", "points": 100},
        "discipline_master": {"name": "纪律大师", "description": "连续10次执行止损", "points": 50},
        "training_10": {"name": "勤学苦练", "description": "完成10次训练", "points": 30},
        "training_50": {"name": "学习达人", "description": "完成50次训练", "points": 100},
        "journal_7days": {"name": "日记达人", "description": "连续7天记录日记", "points": 50},
    }

    # 坏习惯定义
    BAD_HABITS = {
        "扛单": {"severity": "high", "description": "持有亏损仓位不止损"},
        "频繁操作": {"severity": "medium", "description": "过于频繁的开平仓"},
        "过早止盈": {"severity": "low", "description": "盈利未充分发展就平仓"},
        "追涨杀跌": {"severity": "high", "description": "在价格暴涨暴跌时追入"},
        "逆势交易": {"severity": "medium", "description": "与大趋势方向相反交易"},
        "情绪化交易": {"severity": "high", "description": "基于情绪而非分析交易"},
        "过度自信": {"severity": "medium", "description": "连续盈利后加大仓位"},
        "仓位过大": {"severity": "high", "description": "单笔风险超过账户5%"},
        "无止损": {"severity": "high", "description": "开仓时未设置止损"},
        "报复交易": {"severity": "high", "description": "亏损后急于翻本"},
    }

    def __init__(self) -> None:
        _ensure_dir()

    def _load_profile(self) -> Dict[str, Any]:
        """加载用户档案"""
        path = PROFILE_DIR / "profile.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "score": 0,
            "achievements": [],
            "stats": {
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "consecutive_wins": 0,
                "max_consecutive_wins": 0,
                "consecutive_losses": 0,
                "stop_losses_executed": 0,
                "consecutive_stop_losses": 0,
                "trainings_completed": 0,
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    def _save_profile(self, profile: Dict[str, Any]) -> bool:
        """保存用户档案"""
        try:
            profile["updated_at"] = datetime.now().isoformat()
            path = PROFILE_DIR / "profile.json"
            path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"保存用户档案失败: {e}")
            return False

    def get_profile(self) -> Dict[str, Any]:
        """获取用户档案"""
        return self._load_profile()

    def get_level_progress(self) -> Dict[str, Any]:
        """获取等级进度"""
        profile = self._load_profile()
        score = profile.get("score", 0)

        current_level = self.LEVELS[0]
        next_level = None

        for i, lvl in enumerate(self.LEVELS):
            if score >= lvl["min_score"]:
                current_level = lvl
                if i + 1 < len(self.LEVELS):
                    next_level = self.LEVELS[i + 1]

        if next_level:
            progress = (score - current_level["min_score"]) / (next_level["min_score"] - current_level["min_score"]) * 100
            points_to_next = next_level["min_score"] - score
        else:
            progress = 100
            points_to_next = 0

        return {
            "level": current_level["level"],
            "title": current_level["title"],
            "score": score,
            "progress_pct": round(min(100, progress), 1),
            "points_to_next_level": points_to_next,
            "next_level_title": next_level["title"] if next_level else None,
            "total_achievements": len(self.ACHIEVEMENTS),
        }

    def record_trade(self, is_win: bool, stop_loss_executed: bool = False) -> Dict[str, Any]:
        """记录交易结果"""
        logger.info(f"[成长档案] 记录交易: {'盈利' if is_win else '亏损'}, 止损执行: {stop_loss_executed}")
        
        profile = self._load_profile()
        stats = profile.get("stats", {})
        achievements_unlocked = []

        # 更新统计
        stats["total_trades"] = stats.get("total_trades", 0) + 1

        if is_win:
            stats["wins"] = stats.get("wins", 0) + 1
            stats["consecutive_wins"] = stats.get("consecutive_wins", 0) + 1
            stats["consecutive_losses"] = 0
            stats["max_consecutive_wins"] = max(
                stats.get("max_consecutive_wins", 0),
                stats["consecutive_wins"]
            )
            profile["score"] = profile.get("score", 0) + 10
        else:
            stats["losses"] = stats.get("losses", 0) + 1
            stats["consecutive_losses"] = stats.get("consecutive_losses", 0) + 1
            stats["consecutive_wins"] = 0

        if stop_loss_executed:
            stats["stop_losses_executed"] = stats.get("stop_losses_executed", 0) + 1
            stats["consecutive_stop_losses"] = stats.get("consecutive_stop_losses", 0) + 1
            profile["score"] = profile.get("score", 0) + 5
        else:
            stats["consecutive_stop_losses"] = 0

        profile["stats"] = stats

        # 检查成就
        earned = profile.get("achievements", [])

        if stats["total_trades"] == 1 and "first_trade" not in earned:
            earned.append("first_trade")
            achievements_unlocked.append({"key": "first_trade", "message": "🏆 解锁成就：初出茅庐！"})
            profile["score"] += self.ACHIEVEMENTS["first_trade"]["points"]

        if stats["wins"] == 1 and "first_win" not in earned:
            earned.append("first_win")
            achievements_unlocked.append({"key": "first_win", "message": "🏆 解锁成就：初尝胜果！"})
            profile["score"] += self.ACHIEVEMENTS["first_win"]["points"]

        if stats["consecutive_wins"] >= 3 and "win_streak_3" not in earned:
            earned.append("win_streak_3")
            achievements_unlocked.append({"key": "win_streak_3", "message": "🏆 解锁成就：连胜新星！"})
            profile["score"] += self.ACHIEVEMENTS["win_streak_3"]["points"]

        if stats["consecutive_wins"] >= 5 and "win_streak_5" not in earned:
            earned.append("win_streak_5")
            achievements_unlocked.append({"key": "win_streak_5", "message": "🏆 解锁成就：连胜高手！"})
            profile["score"] += self.ACHIEVEMENTS["win_streak_5"]["points"]

        if stats["consecutive_wins"] >= 10 and "win_streak_10" not in earned:
            earned.append("win_streak_10")
            achievements_unlocked.append({"key": "win_streak_10", "message": "🏆 解锁成就：连胜大师！"})
            profile["score"] += self.ACHIEVEMENTS["win_streak_10"]["points"]

        if stats.get("consecutive_stop_losses", 0) >= 10 and "discipline_master" not in earned:
            earned.append("discipline_master")
            achievements_unlocked.append({"key": "discipline_master", "message": "🏆 解锁成就：纪律大师！"})
            profile["score"] += self.ACHIEVEMENTS["discipline_master"]["points"]

        profile["achievements"] = earned
        self._save_profile(profile)

        return {
            "recorded": True,
            "is_win": is_win,
            "achievements_unlocked": achievements_unlocked,
            "current_score": profile["score"],
        }

    def record_training(self) -> Dict[str, Any]:
        """记录训练完成"""
        logger.info("[成长档案] 记录训练完成")
        
        profile = self._load_profile()
        stats = profile.get("stats", {})
        achievements_unlocked = []

        stats["trainings_completed"] = stats.get("trainings_completed", 0) + 1
        profile["score"] = profile.get("score", 0) + 5
        profile["stats"] = stats

        earned = profile.get("achievements", [])

        if stats["trainings_completed"] >= 10 and "training_10" not in earned:
            earned.append("training_10")
            achievements_unlocked.append({"key": "training_10", "message": "🏆 解锁成就：勤学苦练！"})
            profile["score"] += self.ACHIEVEMENTS["training_10"]["points"]

        if stats["trainings_completed"] >= 50 and "training_50" not in earned:
            earned.append("training_50")
            achievements_unlocked.append({"key": "training_50", "message": "🏆 解锁成就：学习达人！"})
            profile["score"] += self.ACHIEVEMENTS["training_50"]["points"]

        profile["achievements"] = earned
        self._save_profile(profile)

        return {
            "recorded": True,
            "trainings_completed": stats["trainings_completed"],
            "achievements_unlocked": achievements_unlocked,
        }

    # ==================== 交易日记 ====================

    def _load_journal(self) -> List[Dict[str, Any]]:
        """加载交易日记"""
        path = PROFILE_DIR / "journal.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

    def _save_journal(self, entries: List[Dict[str, Any]]) -> bool:
        """保存交易日记"""
        try:
            path = PROFILE_DIR / "journal.json"
            path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"保存交易日记失败: {e}")
            return False

    def log_journal_entry(
        self,
        action: str,
        symbol: str = "",
        side: str = "",
        reason: str = "",
        ai_warning: str = "",
        outcome: str = "",
        pnl_pct: float = 0,
        tags: List[str] = None,
    ) -> bool:
        """记录交易日记条目"""
        logger.info(f"[交易日记] {action} {symbol} {side}")
        
        entries = self._load_journal()
        entries.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "symbol": symbol,
            "side": side,
            "reason": reason,
            "ai_warning": ai_warning,
            "outcome": outcome,
            "pnl_pct": pnl_pct,
            "tags": tags or [],
        })

        # 只保留最近1000条
        if len(entries) > 1000:
            entries = entries[-1000:]

        return self._save_journal(entries)

    def get_journal_entries(
        self,
        limit: int = 20,
        symbol: str = "",
        tag: str = "",
    ) -> List[Dict[str, Any]]:
        """获取交易日记条目"""
        entries = self._load_journal()

        if symbol:
            entries = [e for e in entries if symbol.upper() in e.get("symbol", "").upper()]

        if tag:
            entries = [e for e in entries if tag in e.get("tags", [])]

        return entries[-limit:]

    def get_journal_summary(self) -> Dict[str, Any]:
        """获取交易日记统计"""
        entries = self._load_journal()

        # 只统计近30天
        cutoff = datetime.now() - timedelta(days=30)
        recent = [e for e in entries if datetime.fromisoformat(e["timestamp"]) > cutoff]

        wins = sum(1 for e in recent if e.get("outcome") == "win")
        losses = sum(1 for e in recent if e.get("outcome") == "loss")
        ignored_warnings = sum(1 for e in recent if e.get("ai_warning") and e.get("outcome") == "loss")

        return {
            "total_entries": len(recent),
            "wins": wins,
            "losses": losses,
            "ignored_ai_warnings": ignored_warnings,
        }

    # ==================== 坏习惯追踪 ====================

    def _load_habits(self) -> List[Dict[str, Any]]:
        """加载坏习惯记录"""
        path = PROFILE_DIR / "habits.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

    def _save_habits(self, records: List[Dict[str, Any]]) -> bool:
        """保存坏习惯记录"""
        try:
            path = PROFILE_DIR / "habits.json"
            path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"保存坏习惯记录失败: {e}")
            return False

    def add_habit_record(self, habit: str, context: str = "") -> bool:
        """添加坏习惯记录"""
        logger.info(f"[坏习惯] 记录: {habit}")
        
        records = self._load_habits()
        records.append({
            "timestamp": datetime.now().isoformat(),
            "habit": habit,
            "context": context,
        })

        if len(records) > 500:
            records = records[-500:]

        return self._save_habits(records)

    def get_habit_summary(self) -> Dict[str, Any]:
        """获取坏习惯统计"""
        records = self._load_habits()

        # 统计各习惯出现次数
        habit_counts: Dict[str, int] = {}
        for r in records:
            h = r.get("habit", "")
            habit_counts[h] = habit_counts.get(h, 0) + 1

        # 排序
        sorted_habits = sorted(habit_counts.items(), key=lambda x: x[1], reverse=True)

        habits = []
        for h, count in sorted_habits:
            info = self.BAD_HABITS.get(h, {"severity": "low", "description": h})
            habits.append({
                "habit": h,
                "count": count,
                "severity": info["severity"],
                "description": info["description"],
            })

        worst_habit = habits[0]["habit"] if habits else None

        return {
            "total_records": len(records),
            "habits": habits,
            "worst_habit": worst_habit,
        }


__all__ = ["GrowthProfileModule"]

############################################################
# 📘 文件说明：报告状态
# 本文件实现的功能：报告生成状态管理
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
# - 函数: set_send_email_fn, get_send_email_fn, set_notify_switch_fn, get_notify_switch_fn, set_data_providers
#
# 🔗 主要依赖：__future__, typing
#
# 🕒 创建时间：2025-12-18
############################################################

from __future__ import annotations

from typing import Any, Dict, Optional

_SEND_EMAIL_FN: Optional[Any] = None
_NOTIFY_SWITCH_FN: Optional[Any] = None
_DATA_PROVIDERS: Dict[str, Any] = {}


def set_send_email_fn(fn: Optional[Any]) -> None:
    global _SEND_EMAIL_FN
    _SEND_EMAIL_FN = fn


def get_send_email_fn() -> Optional[Any]:
    return _SEND_EMAIL_FN


def set_notify_switch_fn(fn: Optional[Any]) -> None:
    global _NOTIFY_SWITCH_FN
    _NOTIFY_SWITCH_FN = fn


def get_notify_switch_fn() -> Optional[Any]:
    return _NOTIFY_SWITCH_FN


def set_data_providers(providers: Optional[Dict[str, Any]]) -> None:
    global _DATA_PROVIDERS
    _DATA_PROVIDERS = dict(providers or {})


def get_data_providers() -> Dict[str, Any]:
    return _DATA_PROVIDERS


__all__ = [
    "get_data_providers",
    "get_notify_switch_fn",
    "get_send_email_fn",
    "set_data_providers",
    "set_notify_switch_fn",
    "set_send_email_fn",
]

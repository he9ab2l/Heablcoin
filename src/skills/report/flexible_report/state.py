############################################################
# 📘 文件说明：
# 本文件实现的功能：通知与邮件模块：封装消息发送/通知分发能力。
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
# - 依赖（标准库）：__future__, typing
# - 依赖（第三方）：无
# - 依赖（本地）：无
#
# 🕒 创建时间：2025-12-19
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

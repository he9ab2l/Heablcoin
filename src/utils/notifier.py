############################################################
# 📘 文件说明：
# 本文件实现的功能：Notification Utilities
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
# - 依赖（标准库）：__future__, logging, typing
# - 依赖（第三方）：无
# - 依赖（本地）：无
#
# 🕒 创建时间：2025-12-19
############################################################

"""
Notification Utilities
---------------------

This module provides a unified interface for sending notifications
through various channels such as console, email, Telegram, or other
messaging platforms. In v2 the project only supported a single
notification channel hard-coded into the orchestration layer. The
v3 notifier introduces a pluggable architecture that can be extended
to support additional providers with minimal changes. For offline
testing or environments without external connectivity the default
implementation simply logs the notification to stdout.

Usage
-----
```
from utils.notifier import Notifier, ConsoleChannel, TelegramChannel

notifier = Notifier([ConsoleChannel(), TelegramChannel(bot_token='...', chat_id='...')])
notifier.notify("BTC price alert", "Price crossed $50,000!")
```
"""

from __future__ import annotations

from typing import List
import logging


class NotificationChannel:
    """Abstract base class for notification channels."""

    def send(self, title: str, message: str) -> None:
        raise NotImplementedError


class ConsoleChannel(NotificationChannel):
    """Default channel that logs messages to the console."""

    def send(self, title: str, message: str) -> None:
        logging.info("%s: %s", title, message)


try:
    import telegram
except ImportError:
    telegram = None  # type: ignore


class TelegramChannel(NotificationChannel):
    """Sends notifications via Telegram.

    This implementation requires the `python-telegram-bot` package. If it
    is not installed the constructor will raise ImportError.
    """

    def __init__(self, bot_token: str, chat_id: str) -> None:
        if telegram is None:
            raise ImportError("python-telegram-bot is not installed")
        self.bot = telegram.Bot(token=bot_token)
        self.chat_id = chat_id

    def send(self, title: str, message: str) -> None:
        text = f"*{title}*\n{message}"
        self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode='Markdown')


class Notifier:
    """Aggregates multiple channels and sends notifications to all of them."""

    def __init__(self, channels: List[NotificationChannel] | None = None) -> None:
        self.channels: List[NotificationChannel] = channels or [ConsoleChannel()]

    def add_channel(self, channel: NotificationChannel) -> None:
        self.channels.append(channel)

    def notify(self, title: str, message: str) -> None:
        for channel in self.channels:
            try:
                channel.send(title, message)
            except Exception as exc:  # pragma: no cover - do not fail entire notify call
                logging.error("Failed to send notification via %s: %s", channel.__class__.__name__, exc)

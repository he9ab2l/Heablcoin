"""学习模块邮件通知"""
from __future__ import annotations
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from utils.smart_logger import get_logger


logger = get_logger()


def _get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def send_learning_report(
    title: str,
    content: str,
    to_email: Optional[str] = None,
) -> bool:
    """
    发送学习报告邮件
    Args:
        title: 邮件标题
        content: 邮件内容（支持HTML）
        to_email: 收件人邮箱，留空则使用环境变量
    Returns:
        是否发送成功
    """
    smtp_server = _get_env("SMTP_SERVER")
    smtp_port = int(_get_env("SMTP_PORT", "587"))
    smtp_user = _get_env("SMTP_USER") or _get_env("SENDER_EMAIL")
    smtp_pass = _get_env("SMTP_PASS") or _get_env("SENDER_PASSWORD")
    recipient = (
        to_email
        or _get_env("NOTIFY_EMAIL")
        or _get_env("RECIPIENT_EMAIL")
        or _get_env("RECEIVER_EMAIL")
        or smtp_user
    )
    if not all([smtp_server, smtp_user, smtp_pass, recipient]):
        logger.warning("[学习通知] 邮件配置不完整，跳过发送")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Heablcoin学习] {title}"
        msg["From"] = smtp_user
        msg["To"] = recipient
        # 纯文本版本
        text_part = MIMEText(content, "plain", "utf-8")
        msg.attach(text_part)
        # HTML版本（简单转换markdown）
        html_content = _markdown_to_html(content)
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [recipient], msg.as_string())
        logger.learning(f"[学习通知] 邮件发送成功: {title}")
        return True
    except Exception as e:
        logger.error(f"[学习通知] 邮件发送失败: {e}")
        return False


def _markdown_to_html(md: str) -> str:
    """简单的markdown转HTML"""
    html = md
    # 处理标题
    lines = []
    for line in html.split("\n"):
        if line.startswith("### "):
            lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("- "):
            lines.append(f"<li>{line[2:]}</li>")
        elif line.startswith("**") and line.endswith("**"):
            lines.append(f"<strong>{line[2:-2]}</strong>")
        else:
            lines.append(line)
    html = "<br>\n".join(lines)
    # 包装HTML
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; }}
            h3 {{ color: #7f8c8d; }}
            li {{ margin: 5px 0; }}
            .success {{ color: #27ae60; }}
            .warning {{ color: #f39c12; }}
            .error {{ color: #e74c3c; }}
        </style>
    </head>
    <body>
        <div class="container">
            {html}
        </div>
    </body>
    </html>
    """


def send_training_summary(
    session_type: str,
    score: int,
    details: str,
) -> bool:
    """发送训练总结邮件"""
    title = f"训练完成 - {session_type}"
    content = f"""
# 训练总结
**训练类型**: {session_type}
**得分**: {score}/100
## 详情
{details}
---
*此邮件由 Heablcoin 学习模块自动发送*
"""
    return send_learning_report(title, content)


def send_daily_learning_report(
    trainings_completed: int,
    score_gained: int,
    level_info: str,
    habit_warnings: str = "",
) -> bool:
    """发送每日学习报告"""
    title = f"每日学习报告 - 完成{trainings_completed}次训练"
    content = f"""
# 每日学习报告
## 今日成绩
- **完成训练**: {trainings_completed}次
- **获得积分**: {score_gained}分
## 等级信息
{level_info}
## 习惯提醒
{habit_warnings or "✅ 今日无坏习惯记录，继续保持！"}
---
*此邮件由 Heablcoin 学习模块自动发送*
"""
    return send_learning_report(title, content)
__all__ = [
    "send_learning_report",
    "send_training_summary", 
    "send_daily_learning_report",
]

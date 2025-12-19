"""

Email 存储适配器

================

通过邮件发送数据。

"""


from __future__ import annotations


import os

import smtplib

from datetime import datetime

from email.mime.text import MIMEText

from email.mime.multipart import MIMEMultipart

from email.header import Header

from typing import Any, Dict, Optional


from storage.base import StorageTarget, StorageResult, StorageType


class EmailAdapter(StorageTarget):

    """Email 存储适配器"""


    def __init__(

        self,

        smtp_server: Optional[str] = None,

        smtp_port: Optional[int] = None,

        sender_email: Optional[str] = None,

        sender_password: Optional[str] = None,

        recipient_email: Optional[str] = None,

        use_ssl: bool = True,

    ):

        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.qq.com")

        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "465"))

        self.sender_email = sender_email or os.getenv("SENDER_EMAIL") or os.getenv("SMTP_USER", "")

        self.sender_password = sender_password or os.getenv("SENDER_PASSWORD") or os.getenv("SMTP_PASS", "")

        self.recipient_email = (

            recipient_email

            or os.getenv("RECIPIENT_EMAIL")

            or os.getenv("RECEIVER_EMAIL")

            or os.getenv("NOTIFY_EMAIL")

            or self.sender_email

        )

        self.use_ssl = use_ssl


    @property

    def storage_type(self) -> StorageType:

        return StorageType.EMAIL


    def is_available(self) -> bool:

        """检查邮件是否可用"""

        return bool(self.smtp_server and self.sender_email and self.sender_password)


    def _markdown_to_html(self, content: str) -> str:

        """简单的 Markdown 转 HTML"""

        # 尝试使用 markdown 库

        try:

            import markdown

            return markdown.markdown(content, extensions=['tables', 'fenced_code'])

        except ImportError:

            pass


        # 简单转换

        html = content


        # 转换标题

        lines = html.split('\n')

        converted_lines = []

        for line in lines:

            if line.startswith('### '):

                converted_lines.append(f"<h3>{line[4:]}</h3>")

            elif line.startswith('## '):

                converted_lines.append(f"<h2>{line[3:]}</h2>")

            elif line.startswith('# '):

                converted_lines.append(f"<h1>{line[2:]}</h1>")

            elif line.startswith('- ') or line.startswith('* '):

                converted_lines.append(f"<li>{line[2:]}</li>")

            elif line.startswith('**') and line.endswith('**'):

                converted_lines.append(f"<strong>{line[2:-2]}</strong>")

            elif line.strip():

                converted_lines.append(f"<p>{line}</p>")

            else:

                converted_lines.append("<br>")


        return '\n'.join(converted_lines)


    def _create_html_email(self, title: str, content: str) -> str:

        """创建 HTML 邮件"""

        html_content = self._markdown_to_html(content)


        return f"""

<!DOCTYPE html>

<html>

<head>

    <meta charset="utf-8">

    <style>

        body {{

            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

            line-height: 1.6;

            color: #333;

            max-width: 800px;

            margin: 0 auto;

            padding: 20px;

        }}

        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}

        h2 {{ color: #34495e; margin-top: 30px; }}

        h3 {{ color: #7f8c8d; }}

        code {{

            background: #f4f4f4;

            padding: 2px 6px;

            border-radius: 4px;

            font-family: 'Consolas', monospace;

        }}

        pre {{

            background: #2c3e50;

            color: #ecf0f1;

            padding: 15px;

            border-radius: 8px;

            overflow-x: auto;

        }}

        table {{

            border-collapse: collapse;

            width: 100%;

            margin: 20px 0;

        }}

        th, td {{

            border: 1px solid #ddd;

            padding: 12px;

            text-align: left;

        }}

        th {{ background: #3498db; color: white; }}

        tr:nth-child(even) {{ background: #f9f9f9; }}

        .footer {{

            margin-top: 40px;

            padding-top: 20px;

            border-top: 1px solid #eee;

            color: #7f8c8d;

            font-size: 12px;

        }}

    </style>

</head>

<body>

    <h1>{title}</h1>

    {html_content}

    <div class="footer">

        <p>此邮件由 Heablcoin 系统自动发送</p>

        <p>发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    </div>

</body>

</html>

"""


    def _send_email(self, subject: str, html_content: str) -> bool:

        """发送邮件"""

        msg = MIMEMultipart('alternative')

        msg['Subject'] = Header(subject, 'utf-8')

        msg['From'] = self.sender_email

        msg['To'] = self.recipient_email


        # 添加 HTML 内容

        html_part = MIMEText(html_content, 'html', 'utf-8')

        msg.attach(html_part)


        # 发送邮件

        if self.use_ssl:

            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)

        else:

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)

            server.starttls()


        server.login(self.sender_email, self.sender_password)

        server.sendmail(self.sender_email, [self.recipient_email], msg.as_string())

        server.quit()


        return True


    def save_report(self, title: str, content: str, **kwargs) -> StorageResult:

        """通过邮件发送报告"""

        if not self.is_available():

            return StorageResult(

                success=False,

                storage_type=self.storage_type,

                location="",

                error="Email configuration not complete"

            )


        try:

            subject = f"[Heablcoin] {title}"

            html_content = self._create_html_email(title, content)


            self._send_email(subject, html_content)


            return StorageResult(

                success=True,

                storage_type=self.storage_type,

                location=self.recipient_email,

                message=f"Report sent to {self.recipient_email}"

            )


        except Exception as e:

            return StorageResult(

                success=False,

                storage_type=self.storage_type,

                location="",

                error=str(e)

            )


    def save_trade_log(self, data: Dict[str, Any], **kwargs) -> StorageResult:

        """通过邮件发送交易日志"""

        import json


        content = f"""## 交易记录


**交易对**: {data.get('symbol', 'Unknown')}

**方向**: {data.get('side', 'Unknown')}

**数量**: {data.get('amount', 0)}

**价格**: {data.get('price', 0)}

**时间**: {data.get('timestamp', datetime.now().isoformat())}


### 详细数据


```json

{json.dumps(data, ensure_ascii=False, indent=2)}

```

"""

        return self.save_report(

            title=f"交易通知: {data.get('symbol', 'Unknown')}",

            content=content,

            **kwargs

        )


    def save_analysis(self, symbol: str, analysis: Dict[str, Any], **kwargs) -> StorageResult:

        """通过邮件发送分析结果"""

        import json


        content = f"""## 分析摘要


**交易对**: {symbol}

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}


### 分析结果


```json

{json.dumps(analysis, ensure_ascii=False, indent=2)}

```


### 建议


根据以上分析，请结合市场情况做出决策。

"""

        return self.save_report(

            title=f"{symbol} 分析报告",

            content=content,

            **kwargs

        )

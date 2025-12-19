""" 
邮箱配置独立测试（放在 tests/ 目录下统一管理）
注意：此测试会尝试真实连接 SMTP 服务器并发送测试邮件。
- 需要先配置 .env（参考 .env.example）
- 建议先用测试邮箱/授权码
运行方式：
  python tests/test_email_connection.py
或：
  python tests/run_tests.py email
"""
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv


# 添加项目路径
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)


def test_email_connection() -> bool:
    print("=" * 60)
    print("📧 邮箱配置独立测试")
    print("=" * 60)
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    sender = os.getenv("SENDER_EMAIL") or os.getenv("SMTP_USER")
    password = os.getenv("SENDER_PASSWORD") or os.getenv("SMTP_PASS")
    receiver = (
        os.getenv("RECIPIENT_EMAIL")
        or os.getenv("RECEIVER_EMAIL")
        or os.getenv("NOTIFY_EMAIL")
    )
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port_str = os.getenv("SMTP_PORT", "465")
    if not all([sender, password, receiver, smtp_server]):
        print("❌ 错误: .env 文件中缺少必要的邮箱配置。")
        print(f"   SENDER_EMAIL/SMTP_USER: {sender}")
        print(f"   RECIPIENT_EMAIL/RECEIVER_EMAIL/NOTIFY_EMAIL: {receiver}")
        print(f"   SMTP_SERVER: {smtp_server}")
        print("\n👉 你需要设置：EMAIL_NOTIFICATIONS_ENABLED / SENDER_EMAIL 或 SMTP_USER / SENDER_PASSWORD 或 SMTP_PASS / RECIPIENT_EMAIL (或 RECEIVER_EMAIL/NOTIFY_EMAIL) / SMTP_SERVER / SMTP_PORT")
        return False
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        print(f"❌ 错误: SMTP 端口无效: {smtp_port_str}")
        return False
    print("📋 当前配置:")
    print(f"   服务器: {smtp_server}:{smtp_port}")
    print(f"   发件人: {sender}")
    print(f"   收件人: {receiver}")
    masked_pw = f"{password[:2]}...({len(password)}位)" if password else "None"
    print(f"   授权码: {masked_pw}")
    print("-" * 60)
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = "Heablcoin - SMTP Connection Test"
    body = "这是一封测试邮件，用于验证 Heablcoin 的 SMTP 邮件配置是否可用。"
    msg.attach(MIMEText(body, "plain", "utf-8"))
    try:
        print(f"🔄 1. 正在连接到 {smtp_server}...")
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.starttls()
        print("   ✅ 连接成功")
        print(f"🔄 2. 正在登录 ({sender})...")
        server.login(sender, password)
        print("   ✅ 登录成功")
        print("🔄 3. 正在发送邮件...")
        server.send_message(msg)
        print("   ✅ 邮件发送成功")
        server.quit()
        print("\n🎉 测试通过！你的 SMTP 配置可用。")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print("\n❌ 认证失败 (密码/授权码错误):")
        print(f"   错误代码: {getattr(e, 'smtp_code', None)}")
        print(f"   错误信息: {getattr(e, 'smtp_error', None)}")
        print("\n👉 建议: 对于 QQ 邮箱，请确保使用的是'授权码'而不是登录密码。")
        return False
    except smtplib.SMTPConnectError as e:
        print("\n❌ 连接失败:")
        print(f"   错误信息: {e}")
        print("\n👉 建议: 检查 SMTP_SERVER/SMTP_PORT，或网络是否拦截端口。")
        return False
    except Exception as e:
        print("\n❌ 发送过程中发生未知错误:")
        print(f"   类型: {type(e).__name__}")
        print(f"   详细信息: {e}")
        return False


def run_all_tests() -> bool:
    ok = test_email_connection()
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {1 if ok else 0} 通过, {0 if ok else 1} 失败")
    print("=" * 60)
    return ok
if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

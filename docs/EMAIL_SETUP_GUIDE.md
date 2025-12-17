# 📧 邮箱授权码配置指南

交易通知功能需要配置 SMTP 邮箱。本指南介绍如何获取各主流邮箱的授权码。

## QQ 邮箱 (推荐)

1. 登录 [QQ邮箱](https://mail.qq.com)
2. 进入 **设置** → **账户**
3. 找到 **POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务**
4. 开启 **IMAP/SMTP服务**
5. 按提示发送短信验证
6. 获取 **16位授权码**

```env
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465
SENDER_EMAIL=你的QQ号@qq.com
SENDER_PASSWORD=你的16位授权码
```

## Gmail

1. 访问 [Google 账号安全设置](https://myaccount.google.com/security)
2. 开启 **两步验证**
3. 访问 [应用专用密码](https://myaccount.google.com/apppasswords)
4. 选择 **邮件** + **Windows 计算机**
5. 复制生成的 **16位密码**

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=你的邮箱@gmail.com
SENDER_PASSWORD=你的16位应用密码
```

## 163 邮箱

1. 登录 [163邮箱](https://mail.163.com)
2. 进入 **设置** → **POP3/SMTP/IMAP**
3. 开启 **IMAP/SMTP服务**
4. 设置 **客户端授权密码**

```env
SMTP_SERVER=smtp.163.com
SMTP_PORT=465
SENDER_EMAIL=你的邮箱@163.com
SENDER_PASSWORD=你的授权密码
```

## ⚠️ 重要提醒

- **不要使用登录密码**，必须使用授权码/应用专用密码
- 授权码只显示一次，请妥善保存
- 如果发送失败，检查是否被邮箱安全策略拦截

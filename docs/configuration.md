# 配置指南 ⚙️

Heablcoin 使用 `.env` 文件管理敏感配置和系统行为。这确保你的密钥（如 API Key）不会被硬编码在源代码中。

---

## 配置步骤

1.  在项目根目录找到 `.env.example` 文件
2.  复制并重命名为 `.env`
3.  用文本编辑器打开 `.env`，按下面的说明填写

---

## 环境变量详解

### 🏦 交易所配置

控制与 Binance 交易所的连接。

| 变量名 | 必填 | 说明 |
| :--- | :--- | :--- |
| `BINANCE_API_KEY` | ✅ 是 | 你的 Binance API Key |
| `BINANCE_SECRET_KEY` | ✅ 是 | 你的 Binance API Secret |
| `USE_TESTNET` | ✅ 是 | `True` 使用测试网（安全，推荐）；`False` 使用主网（真实资金） |

> **安全提示**: 永远不要将 `.env` 文件提交到版本控制系统（如 Git）。

#### 如何获取 API Key

**测试网（推荐新手）**:
1. 访问 https://testnet.binance.vision/
2. 使用 GitHub 账号登录
3. 点击 "Generate HMAC_SHA256 Key"
4. 复制生成的 API Key 和 Secret Key

**主网（真实交易）**:
1. 登录 https://www.binance.com/
2. 进入「用户中心」→「API 管理」
3. 创建新的 API Key
4. **重要**: 仅开启「现货交易」权限，关闭提现权限

---

### 📧 邮件通知配置

配置这些参数后，可通过邮件接收交易提醒和每日报告。

| 变量名 | 必填 | 说明 |
| :--- | :--- | :--- |
| `EMAIL_NOTIFICATIONS_ENABLED` | 否 | 设为 `True` 启用邮件功能，默认 `False` |
| `SENDER_EMAIL` | 启用时必填 | 发送邮件的邮箱地址（如 QQ 邮箱） |
| `SENDER_PASSWORD` | 启用时必填 | **授权码**（不是登录密码！） |
| `RECEIVER_EMAIL` | 启用时必填 | 接收通知的邮箱地址 |
| `SMTP_SERVER` | 启用时必填 | SMTP 服务器地址 |
| `SMTP_PORT` | 启用时必填 | SMTP 端口（通常 SSL 用 `465`） |

#### 常用邮箱 SMTP 配置

| 邮箱 | SMTP 服务器 | 端口 |
| :--- | :--- | :--- |
| QQ 邮箱 | `smtp.qq.com` | 465 |
| 163 邮箱 | `smtp.163.com` | 465 |
| Gmail | `smtp.gmail.com` | 465 或 587 |

#### 如何获取 QQ 邮箱授权码

1. 登录 QQ 邮箱 → 设置 → 账户
2. 找到「POP3/IMAP/SMTP 服务」
3. 开启「IMAP/SMTP 服务」
4. 按提示发送短信验证
5. 获取 16 位授权码，填入 `SENDER_PASSWORD`

---

### 🛡️ 风险管理与交易限额

保护你的资金安全的重要设置。

| 变量名 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `MAX_TRADE_AMOUNT` | 否 | `1000.0` | 单笔交易最大金额（USDT） |
| `DAILY_TRADE_LIMIT` | 否 | `5000.0` | 每日交易累计限额（USDT） |
| `ALLOWED_SYMBOLS` | 否 | （见下方） | 允许交易的币种白名单，逗号分隔 |

**默认白名单币种**:
```
BTC/USDT,ETH/USDT,BNB/USDT,SOL/USDT,XRP/USDT,
ADA/USDT,DOT/USDT,DOGE/USDT,AVAX/USDT,LINK/USDT,
MATIC/USDT,UNI/USDT,ATOM/USDT,LTC/USDT,ETC/USDT
```

不在白名单内的交易对将被自动拒绝。

---

### 🔧 系统与日志

| 变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `LOG_LEVEL` | `INFO` | 日志级别：`DEBUG`（最详细）、`INFO`、`WARNING`、`ERROR` |
| `LOG_FILE` | `server_debug.log` | 日志输出文件名，位于 `logs/` 目录 |

---

### 🔔 精细化通知开关

在不关闭全局邮件的情况下，单独控制特定类型的通知。

| 变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `NOTIFY_TRADE_EXECUTION` | `True` | 交易执行成功时发送通知 |
| `NOTIFY_PRICE_ALERTS` | `True` | 价格预警触发时发送通知 |
| `NOTIFY_DAILY_REPORT` | `True` | 生成每日报告时发送通知 |
| `NOTIFY_SYSTEM_ERRORS` | `True` | 系统异常时发送通知 |

---

## 完整配置示例

```ini
# === 交易所 ===
BINANCE_API_KEY=你的API_Key
BINANCE_SECRET_KEY=你的Secret_Key
USE_TESTNET=True

# === 邮件 ===
EMAIL_NOTIFICATIONS_ENABLED=True
SENDER_EMAIL=你的QQ邮箱@qq.com
SENDER_PASSWORD=你的16位授权码
RECEIVER_EMAIL=接收通知的邮箱@example.com
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465

# === 风控 ===
ALLOWED_SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT
MAX_TRADE_AMOUNT=500
DAILY_TRADE_LIMIT=2000

# === 日志 ===
LOG_LEVEL=INFO
```

---

## 配置完成后

 运行以下命令验证配置是否正确：
 
 ```bash
 python tests/run_tests.py --quick
 ```

如果看到 "✅ 连接成功!"，说明配置无误！

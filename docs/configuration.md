# 配置指南 ⚙️

Heablcoin 使用 `.env` 管理所有敏感和可调参数。请始终基于 `./.env.example` 复制生成 `.env`，并确保该文件不进入版本控制。

## 快速上手
1) 复制模板：`cp .env.example .env`  
2) 填写必填项：交易所密钥、`USE_TESTNET`、邮件账户、至少一个 AI 提供商密钥（可选，未填则回退离线 echo）。  
3) 安装依赖：`pip install -r requirements.txt`  
4) 验证：`python tests/run_tests.py --quick`（邮件链路可用 `python tests/run_tests.py email`）。

## 变量分组速查

### 交易所 / CCXT
- `BINANCE_API_KEY` / `BINANCE_SECRET_KEY`：交易所密钥。
- `USE_TESTNET`：是否使用币安测试网（强烈推荐先用测试网）。
- `EXCHANGE_POOL_TTL_SECONDS`：交易所连接池复用时间。
- `CCXT_TIMEOUT_MS`，`CCXT_ENABLE_RATE_LIMIT`，`CCXT_DEFAULT_TYPE`，`CCXT_RECV_WINDOW`，`CCXT_ADJUST_TIME_DIFFERENCE`：CCXT 连接超时、限流与时间校准参数。

### 🤖 AI 提供商（多云可选填其一或多项）

| 变量 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` / `OPENAI_MODEL` / `OPENAI_BASE_URL` | `gpt-4o-mini` / `https://api.openai.com/v1` | OpenAI / 兼容端点 |
| `DEEPSEEK_API_KEY` / `DEEPSEEK_MODEL` / `DEEPSEEK_BASE_URL` | `deepseek-chat` / `https://api.deepseek.com/v1` | DeepSeek |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` / `ANTHROPIC_BASE_URL` | `claude-3-haiku-20240307` / `https://api.anthropic.com/v1/messages` | Anthropic |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | `gemini-1.5-flash` | Google Gemini |
| `GROQ_API_KEY` / `GROQ_MODEL` / `GROQ_BASE_URL` | `llama-3.1-70b-versatile` / `https://api.groq.com/openai/v1` | Groq（OpenAI 兼容） |
| `MOONSHOT_API_KEY` / `MOONSHOT_MODEL` / `MOONSHOT_BASE_URL` | `moonshot-v1-8k` / `https://api.moonshot.cn/v1` | Moonshot Kimi（OpenAI 兼容） |
| `ZHIPU_API_KEY` / `ZHIPU_MODEL` / `ZHIPU_BASE_URL` | `glm-4` / `https://open.bigmodel.cn/api/paas/v4` | 智谱 GLM（OpenAI 兼容） |
| `HEABL_*` keys | 同上 | 也可使用 HEABL_OPENAI_KEY / HEABL_DEEPSEEK_KEY / HEABL_GEMINI_KEY / HEABL_MOONSHOT_KEY / HEABL_GROQ_KEY / HEABL_ZHIPU_KEY / HEABL_DOUBAO_KEY 等 |
| `HEABL_DOUBAO_BASE` / `HEABL_DOUBAO_MODEL` | `https://ark.cn-beijing.volces.com/api/v3` / `ep-202406140015` | 字节 Doubao (OpenAI 兼容) |
| `HEABL_COOLYEAH_BASE` / `HEABL_COOLYEAH_MODEL` | `https://api.coolyeah.com/v1` / `gpt-4o-mini` | 自定义 OpenAI 兼容端点 |
| `AI_TIMEOUT` | `30` | AI 请求超时（秒） |
| `AI_DEFAULT_PROVIDER` | 空 | 默认 provider 名称（openai/deepseek/anthropic/gemini/groq/moonshot/zhipu/doubao/coolyeah/echo） |
| `HEABL_LLM_DEFAULT` / `HEABL_LLM_PREFERENCE` | 空 | LLM Router 优先级列表，逗号分隔；未填则按可用 provider 逐个尝试 |
| `AI_ROUTE_ANALYSIS` / `AI_ROUTE_CRITIQUE` / `AI_ROUTE_SYNTHESIS` / `AI_ROUTE_SAFETY` | 空 | 为多角色路由指定 provider 名称 |

未配置任何密钥时，系统自动回退到离线 echo provider，保证流程可用。

### 📧 邮件通知

| 变量 | 必填 | 说明 |
| :--- | :--- | :--- |
| `EMAIL_NOTIFICATIONS_ENABLED` | 否 | `True` 开启邮件功能 |
| `SENDER_EMAIL` / `SENDER_PASSWORD` | 启用时必填 | 发件邮箱与授权码（默认也作为 `SMTP_USER`/`SMTP_PASS`） |
| `SMTP_USER` / `SMTP_PASS` | 可选 | 登录账号/密码，如与发件人不同可单独填写 |
| `RECIPIENT_EMAIL` | 启用时必填 | 收件邮箱，兼容 `RECEIVER_EMAIL` / `NOTIFY_EMAIL` |
| `SMTP_SERVER` / `SMTP_PORT` | 启用时必填 | SMTP 地址与端口（SSL 常用 `465`） |

兼容性：老版本使用的 `RECEIVER_EMAIL` / `NOTIFY_EMAIL` 仍被支持，但推荐统一使用 `RECIPIENT_EMAIL`。

常用 SMTP：
- QQ：`smtp.qq.com`，端口 `465`
- 163：`smtp.163.com`，端口 `465`
- Gmail：`smtp.gmail.com`，端口 `465` 或 `587`

### 🛡 风控与市场数据

| 变量 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `MAX_TRADE_AMOUNT` | `1000.0` | 单笔最大交易额（USDT） |
| `DAILY_TRADE_LIMIT` | `5000.0` | 每日累计交易限额（USDT） |
| `ALLOWED_SYMBOLS` | 见 `.env.example` | 交易对白名单，逗号分隔 |

行情拉取上限（按模块分开配置）：  
`OHLCV_LIMIT_MARKET_ANALYSIS`，`OHLCV_LIMIT_COMPREHENSIVE_ANALYSIS`，`OHLCV_LIMIT_SENTIMENT`，`OHLCV_LIMIT_OVERVIEW`，`OHLCV_LIMIT_MARKET_OVERVIEW`，`OHLCV_LIMIT_SIGNALS`，`OHLCV_LIMIT_STRATEGY`

### 💾 存储与外部集成

| 变量 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `ENABLE_TRADE_DB` | `True` | 启用 SQLite 交易库（失败时自动回退 CSV） |
| `TRADE_DB_FILE` | `data/trades.db` | 交易数据库路径 |
| `NOTION_API_KEY` | 空 | 开启 Notion 适配器所需 |
| `NOTION_DATABASE_ID` | 空 | 主 Notion 数据库 |
| `NOTION_REPORTS_DB_ID` / `NOTION_TRADES_DB_ID` | 同上 | 可选：报告/交易分库 ID |

### 📓 日志与性能

| 变量 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `DEBUG_MODE` | `False` | 输出更详细的调试信息 |
| `LOG_LEVEL` | `INFO` | 日志级别（DEBUG/INFO/WARNING/ERROR） |
| `LOG_FILE` | `logs/server_debug.log` | 传统日志文件 |
| `LOG_DIR` | `logs` | 智能日志/性能数据目录 |
| `LOG_ROTATE_MAX_BYTES` / `LOG_ROTATE_BACKUP_COUNT` | `5242880` / `3` | 传统日志滚动配置 |
| `ENABLE_SMART_LOGGER` / `ENABLE_SMART_CACHE` | `True` | 是否启用智能日志 / 智能缓存 |
| `PERF_SLOW_THRESHOLD_SECONDS` | `3.0` | 慢调用阈值 |
| `PERF_DEGRADATION_FACTOR` / `PERF_DEGRADATION_MIN_CALLS` | `2.0` / `10` | 性能下降判定参数 |
| `CACHE_DEFAULT_TTL_SECONDS` | `300` | 智能缓存默认 TTL |
| `SERVER_ID` | 空 | 可选：覆盖节点标识 |

### 🔔 通知开关（精细化）
- `NOTIFY_TRADE_EXECUTION`：成交通知  
- `NOTIFY_PRICE_ALERTS`：价格预警通知  
- `NOTIFY_DAILY_REPORT`：日报/报告通知  
- `NOTIFY_SYSTEM_ERRORS`：系统错误通知

### 🛰 云端 Pipeline / 青龙
- `REDIS_URL` 或 (`REDIS_HOST`/`REDIS_PORT`/`REDIS_PASSWORD`)
- `TASK_QUEUE_KEY`（默认 `mcp:tasks`）、`RESULT_HASH_KEY`（默认 `mcp:results`）
- `NOTIFY_DEFAULT`、`NOTIFY_FAILOVER`
- `HEABL_TAVILY_KEY`（搜索）、多云 LLM Key（总结）
- `RUN_ONCE`（默认 true，青龙设为 false 持续轮询）、`WORKER_INTERVAL`

## 示例配置片段

```ini
# 交易所
BINANCE_API_KEY=your_key
BINANCE_SECRET_KEY=your_secret
USE_TESTNET=True

# AI（按需填写）
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=

# 邮件
EMAIL_NOTIFICATIONS_ENABLED=True
SENDER_EMAIL=you@example.com
SENDER_PASSWORD=app_password
RECIPIENT_EMAIL=alert@example.com
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465

# 风控
MAX_TRADE_AMOUNT=500
DAILY_TRADE_LIMIT=2000
ALLOWED_SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT
```

## 配置完成后
- 运行 `python tests/run_tests.py --quick` 快速检查交易所与核心模块。
- 运行 `python tests/run_tests.py email` 验证 SMTP 链路（可能会发送真实邮件）。
- 使用 MCP 客户端前，确保 `.env` 已填好且 Python 依赖已安装。

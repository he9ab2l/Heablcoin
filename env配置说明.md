# 环境变量与 `.env` 配置说明

Heablcoin 使用项目根目录的 `.env` 管理所有敏感和可调参数。

约定：
- `.env` **不要提交**到 Git（仅提交 `.env.example` 模板）。
- 文档与配置说明统一使用 UTF-8（无 BOM）。

## 1. 快速开始（必读）

1) 从模板复制：

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

2) 填写交易所密钥与运行模式（建议测试网 / paper 模式起步）。

3) 运行自检：

```bash
python tests/run_tests.py unit
```

如需验证邮件链路（可能会发送真实邮件）：

```bash
python tests/run_tests.py email
```

## 2. 加载与优先级

- 系统会在启动时加载 `PROJECT_ROOT/.env`（见 `src/core/server.py` 中的 `load_dotenv(...)`）。
- 通常遵循：**系统环境变量优先于 `.env`**（避免生产环境被本地文件覆盖）。
- `.env.example` 是“变量清单 + 默认值”的权威模板；不确定时以它为准。

## 3. 变量分组说明（按用途）

### 3.1 交易所 / CCXT（常用必填）

- `BINANCE_API_KEY` / `BINANCE_SECRET_KEY`：交易所密钥。
- `USE_TESTNET`：是否使用测试网（强烈建议先 `True`）。
- `EXCHANGE_POOL_TTL_SECONDS`：交易所连接池复用时间。
- `CCXT_TIMEOUT_MS`：请求超时。
- `CCXT_ENABLE_RATE_LIMIT`：是否启用 CCXT 内置限流。
- `CCXT_DEFAULT_TYPE`：`spot`/`future` 等。
- `CCXT_RECV_WINDOW`：交易所接收窗口。
- `CCXT_ADJUST_TIME_DIFFERENCE`：是否自动校时。

### 3.2 AI 提供商（可选，未配置会回退离线 echo）

任选其一或多个提供商，系统会按可用配置进行路由。

| 变量 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` / `OPENAI_MODEL` / `OPENAI_BASE_URL` | `gpt-4o-mini` / `https://api.openai.com/v1` | OpenAI / 兼容端点 |
| `DEEPSEEK_API_KEY` / `DEEPSEEK_MODEL` / `DEEPSEEK_BASE_URL` | `deepseek-chat` / `https://api.deepseek.com/v1` | DeepSeek |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` / `ANTHROPIC_BASE_URL` | `claude-3-haiku-20240307` / `https://api.anthropic.com/v1/messages` | Anthropic |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini |
| `GROQ_API_KEY` / `GROQ_MODEL` / `GROQ_BASE_URL` | `llama-3.1-70b-versatile` / `https://api.groq.com/openai/v1` | Groq（OpenAI 兼容） |
| `MOONSHOT_API_KEY` / `MOONSHOT_MODEL` / `MOONSHOT_BASE_URL` | `moonshot-v1-8k` / `https://api.moonshot.cn/v1` | Moonshot（OpenAI 兼容） |
| `ZHIPU_API_KEY` / `ZHIPU_MODEL` / `ZHIPU_BASE_URL` | `glm-4` / `https://open.bigmodel.cn/api/paas/v4` | 智谱（OpenAI 兼容） |
| `HEABL_*` keys | 同上 | 也可使用 `HEABL_OPENAI_KEY` / `HEABL_DEEPSEEK_KEY` / `HEABL_GEMINI_KEY` / `HEABL_MOONSHOT_KEY` / `HEABL_GROQ_KEY` / `HEABL_ZHIPU_KEY` / `HEABL_DOUBAO_KEY` / `HEABL_COOLYEAH_KEY` 等 |
| `HEABL_DOUBAO_BASE` / `HEABL_DOUBAO_MODEL` | `https://ark.cn-beijing.volces.com/api/v3` / `ep-202406140015` | Doubao（OpenAI 兼容） |
| `HEABL_COOLYEAH_BASE` / `HEABL_COOLYEAH_MODEL` | `https://api.coolyeah.com/v1` / `gpt-4o-mini` | 自定义 OpenAI 兼容端点 |
| `AI_TIMEOUT` | `30` | AI 请求超时（秒） |
| `AI_DEFAULT_PROVIDER` | 空 | 默认 provider（openai/deepseek/anthropic/gemini/groq/moonshot/zhipu/doubao/coolyeah/echo） |
| `HEABL_LLM_DEFAULT` / `HEABL_LLM_PREFERENCE` | 空 | LLM Router 优先级列表（逗号分隔） |
| `AI_ROUTE_ANALYSIS` / `AI_ROUTE_CRITIQUE` / `AI_ROUTE_SYNTHESIS` / `AI_ROUTE_SAFETY` | 空 | 为多角色路由指定 provider 名称 |

### 3.3 邮件通知（可选）

| 变量 | 必填 | 说明 |
| :--- | :--- | :--- |
| `EMAIL_NOTIFICATIONS_ENABLED` | 否 | `True` 开启邮件功能 |
| `SENDER_EMAIL` / `SENDER_PASSWORD` | 启用时必填 | 发件邮箱与授权码（也可作为 `SMTP_USER`/`SMTP_PASS`） |
| `SMTP_USER` / `SMTP_PASS` | 可选 | 登录账号/密码，如与发件人不同可单独填写 |
| `RECIPIENT_EMAIL` | 启用时必填 | 收件邮箱（兼容 `RECEIVER_EMAIL` / `NOTIFY_EMAIL`） |
| `SMTP_SERVER` / `SMTP_PORT` | 启用时必填 | SMTP 地址与端口（SSL 常用 `465`） |

常用 SMTP：
- QQ：`smtp.qq.com`，端口 `465`
- 163：`smtp.163.com`，端口 `465`
- Gmail：`smtp.gmail.com`，端口 `465` 或 `587`

### 3.4 风控与市场数据（建议至少设置限额）

| 变量 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `MAX_TRADE_AMOUNT` | `1000.0` | 单笔最大交易额（USDT） |
| `DAILY_TRADE_LIMIT` | `5000.0` | 每日累计交易限额（USDT） |
| `ALLOWED_SYMBOLS` | 见 `.env.example` | 交易对白名单，逗号分隔 |

行情拉取上限（按模块分开配置）：
`OHLCV_LIMIT_MARKET_ANALYSIS`，`OHLCV_LIMIT_COMPREHENSIVE_ANALYSIS`，`OHLCV_LIMIT_SENTIMENT`，`OHLCV_LIMIT_OVERVIEW`，`OHLCV_LIMIT_MARKET_OVERVIEW`，`OHLCV_LIMIT_SIGNALS`，`OHLCV_LIMIT_STRATEGY`

### 3.5 存储与外部集成（可选）

| 变量 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `ENABLE_TRADE_DB` | `True` | 启用 SQLite 交易库（失败时自动回退 CSV） |
| `TRADE_DB_FILE` | `data/trades.db` | 交易数据库路径 |
| `NOTION_API_KEY` | 空 | 开启 Notion 适配器所需 |
| `NOTION_DATABASE_ID` | 空 | 主 Notion 数据库 |
| `NOTION_REPORTS_DB_ID` / `NOTION_TRADES_DB_ID` | 空 | 可选：报告/交易分库 ID |

### 3.6 Redis / 任务队列 / 云端 Pipeline（可选）

优先使用：
- `REDIS_URL`

或拆分配置：
- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_PASSWORD`（或 `REDIS_PASS`）
- `REDIS_SSL`

队列/结果键：
- `TASK_QUEUE_KEY`（默认 `mcp:tasks`）
- `RESULT_HASH_KEY`（默认 `mcp:results`）

通知通道（逗号分隔）：
- `NOTIFY_DEFAULT`（默认 `serverchan`）
- `NOTIFY_FAILOVER`（默认 `serverchan`）

### 3.7 日志与性能（可选但强烈建议保留默认）

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

### 3.8 MCP 调用审计与备份（可选）

用于“每次 MCP 工具调用”的审计日志与自动备份（可关闭）。为避免泄露敏感信息，参数会按 key 名称做脱敏（如 `api_key`/`secret`/`password` 等）。

| 变量 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `MCP_FORCE_PRINT_TO_STDERR` | `True` | 是否将未显式指定 `file` 的 `print()` 重定向到 stderr（推荐开启，避免污染 MCP 协议通道） |
| `MCP_REDIRECT_STDOUT` | `False` | 是否将 `sys.stdout` 重定向到 stderr（高风险：可能破坏 MCP stdio 协议；默认关闭） |
| `MCP_CALL_LOG_ENABLED` | `True` | 是否记录 MCP 调用日志（写入 `logs/mcp.log`，结构化 JSON） |
| `MCP_CALL_LOG_INCLUDE_ARGS` | `True` | 是否记录调用参数（会脱敏） |
| `MCP_CALL_LOG_MAX_VALUE_CHARS` | `2000` | 参数字段字符串截断长度 |
| `MCP_CALL_LOG_MAX_RESULT_CHARS` | `2000` | 返回值预览截断长度 |
| `MCP_CALL_BACKUP_ENABLED` | `True` | 是否落盘备份每次调用（JSON） |
| `MCP_CALL_BACKUP_DIR` | `data/mcp_call_backups` | 备份目录（按天分目录） |
| `MCP_CALL_BACKUP_MAX_RESULT_CHARS` | `20000` | 备份中返回值截断长度 |
| `MCP_CALL_BACKUP_INCLUDE_TRACEBACK` | `False` | 是否在失败备份中写入 traceback（默认关闭） |

### 3.9 通知开关（精细化，可选）

- `NOTIFY_TRADE_EXECUTION`：成交通知
- `NOTIFY_PRICE_ALERTS`：价格预警通知
- `NOTIFY_DAILY_REPORT`：日报/报告通知
- `NOTIFY_SYSTEM_ERRORS`：系统错误通知

### 3.10 MCP Tools 开关（软禁用，可选）

- `TOOLS_DISABLED`：逗号分隔黑名单（工具会返回禁用提示，不执行真实逻辑）
- `TOOLS_ENABLED_ONLY`：逗号分隔白名单（非空时仅白名单启用）

### 3.11 其他通知通道（可选）

- Server酱：`SERVERCHAN_SENDKEY`
- 飞书：`FEISHU_WEBHOOK`、`FEISHU_SECRET`（可选签名）

### 3.12 搜索（可选）

用于云端 Pipeline 检索/摘要：
- `HEABL_TAVILY_KEY`（或 `TAVILY_API_KEY`）

## 4. 示例配置片段

```ini
# 交易所
BINANCE_API_KEY=your_key
BINANCE_SECRET_KEY=your_secret
USE_TESTNET=True

# AI（按需填写，未填会回退离线 echo）
OPENAI_API_KEY=
DEEPSEEK_API_KEY=

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

## 5. 配置完成后

- 运行 `python tests/run_tests.py unit` 快速检查核心模块与单元测试。
- 如需验证交易所连通性（可能需要联网与交易所配置），运行 `python Heablcoin-test.py --quick`。
- 运行 `python tests/run_tests.py email` 验证 SMTP 链路（可能会发送真实邮件）。
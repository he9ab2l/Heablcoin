# Heablcoin 项目说明

面向个人量化交易助手的 MCP 服务器，提供市场分析、自动交易、个人绩效、学习训练、报告与通知的全链路能力，并支持多云 AI 供应商路由。

## 核心特性
- **MCP 标准化**：FastMCP 入口，工具均带异常防护，避免 stdout 污染。
- **多模型路由**：OpenAI/DeepSeek/Anthropic/Gemini/Groq/Moonshot/智谱 GLM 等，`AI_ROUTE_*` 按角色分流，`AI_DEFAULT_PROVIDER` 兜底。
- **交易安全**：白名单 `ALLOWED_SYMBOLS`、`MAX_TRADE_AMOUNT`、`DAILY_TRADE_LIMIT`，支持测试网/主网切换。
- **分析矩阵**：技术、情绪、信号、市场全景、AI 建议、仓位建议，支持可视化返回。
- **存储与同步**：SQLite/CSV 交易存储，Notion/Email/File 适配器并行保存报告。
- **云端协同**：Redis + 青龙哨兵，`set_cloud_sentry` 可写入云端监控队列；`consult_external_expert` 调用外部 AI；`sync_session_to_notion` 记录会话。
- **学习与通知**：学习模块邮件推送；智能日志/缓存监控，性能阈值可调。

## 目录结构
- `Heablcoin.py`：MCP 主入口，加载环境、日志、缓存、工具注册。
- `orchestration/`：多 AI 编排、角色定义、路由与 MCP 工具。
- `cloud/`：API 管理器、多端点负载/容错。
- `market_analysis/`：行情获取、指标、信号、情绪、全景输出。
- `personal_analytics/`：交易历史/绩效读取与标准化。
- `learning/`：训练/学习通知。
- `report/`：灵活报告生成与邮件发送。
- `storage/`：File/Notion/Email 适配器与管理器。
- `utils/`：智能日志、缓存、交易存储等通用组件。
- `docs/`：配置、安装、API 参考及本说明。
- `tests/`：连接、邮箱、MCP 工具等回归脚本。

## 环境配置要点（.env）
- 交易：`BINANCE_API_KEY`/`BINANCE_SECRET_KEY`，`USE_TESTNET`。
- AI：`OPENAI_*`、`DEEPSEEK_*`、`ANTHROPIC_*`、`GEMINI_*`、`GROQ_*`、`MOONSHOT_*`、`ZHIPU_*`，以及 `AI_DEFAULT_PROVIDER`、`AI_ROUTE_*`。
- 风控与行情：`ALLOWED_SYMBOLS`、`MAX_TRADE_AMOUNT`、`DAILY_TRADE_LIMIT`、`OHLCV_LIMIT_*`、`CCXT_*`。
- 邮件：`EMAIL_NOTIFICATIONS_ENABLED`、`SENDER_EMAIL`/`SENDER_PASSWORD`（或 `SMTP_USER`/`SMTP_PASS`）、`RECIPIENT_EMAIL`（兼容旧变量）。
- 日志/性能：`LOG_LEVEL`、`LOG_FILE`、`LOG_DIR`、`ENABLE_SMART_LOGGER`、`ENABLE_SMART_CACHE`、`PERF_*`、`CACHE_DEFAULT_TTL_SECONDS`。
- 存储/集成：`ENABLE_TRADE_DB`、`TRADE_DB_FILE`、`NOTION_*`。

## 使用与测试
- **MCP 客户端**：在 Claude/Windsurf 配置指向 `python d:/MCP/Heablcoin.py`（绝对路径），并设置 UTF-8 环境。
- **终端测试**：`python tests/run_tests.py --quick` 快速回归；`python tests/run_tests.py email` 验证 SMTP。
- **常用工具**：`ai_run_pipeline`（多阶段 AI）、`ai_call_role`/`ai_reason`/`ai_write` 等角色调用；市场分析与交易工具详见 `docs/api_reference.md`。
- **云端工具**：`consult_external_expert`（多云外脑）、`set_cloud_sentry`（Redis 哨兵）、`sync_session_to_notion`、`fetch_portfolio_snapshot`、`get_learning_context`（dev/lessons 注入）。

## 运行建议
- 开发：保持 `USE_TESTNET=True`，先跑 quick 测试；需要邮件时开启 `EMAIL_NOTIFICATIONS_ENABLED` 并填写 SMTP。
- 生产/云：将 `.env` 迁移到 Secrets/Config，使用进程守护或容器化，并集中收集 `LOG_DIR`。
- 多模型：按角色设置 `AI_ROUTE_*`，确保每个 provider 的 Key 与 Base URL 已填。

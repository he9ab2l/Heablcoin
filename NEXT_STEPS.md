# 下一步行动与云端升级指南

## 立即要做的事（优先顺序）
1. 复制并更新环境：`cp .env.example .env`，填入交易所密钥、邮件账号，至少保留一个 AI 提供商密钥（缺省会回退离线 echo）。  
2. 安装依赖并自检：`pip install -r requirements.txt`，运行 `python tests/run_tests.py --quick`。  
3. 验证邮件链路（可选）：`python tests/run_tests.py email`，确认 `RECIPIENT_EMAIL`/`SMTP_USER` 配置正确。  
4. 检查风控阈值：`MAX_TRADE_AMOUNT`、`DAILY_TRADE_LIMIT`、`ALLOWED_SYMBOLS` 是否符合预期。  
5. 如需知识/数据落地：准备好 `NOTION_API_KEY` 与 `NOTION_DATABASE_ID`，或确认 `TRADE_DB_FILE` 目录可写。

## 配置要点（速查）
- 交易所：`BINANCE_API_KEY`、`BINANCE_SECRET_KEY`、`USE_TESTNET`。  
- 邮件：首选 `RECIPIENT_EMAIL`，兼容 `RECEIVER_EMAIL`/`NOTIFY_EMAIL`；`SENDER_EMAIL`/`SENDER_PASSWORD` 可作为 `SMTP_USER`/`SMTP_PASS` 默认值。  
- AI 选择：`AI_DEFAULT_PROVIDER` 决定默认调用；`AI_ROUTE_ANALYSIS`/`AI_ROUTE_CRITIQUE`/`AI_ROUTE_SYNTHESIS`/`AI_ROUTE_SAFETY` 可为多角色指定不同 provider。  
- 日志/性能：`LOG_DIR`、`LOG_FILE`、`ENABLE_SMART_LOGGER`、`ENABLE_SMART_CACHE`、`PERF_SLOW_THRESHOLD_SECONDS`、`CACHE_DEFAULT_TTL_SECONDS`。  
- 市场数据：`OHLCV_LIMIT_*` 系列控制各分析模块的 K 线拉取条数；`CCXT_*` 决定连通性和限流。  
- 存储与集成：`ENABLE_TRADE_DB`、`TRADE_DB_FILE`、`NOTION_*`。

## 云端升级路线（建议循序推进）
1. **容器化基础**：写一个轻量 `Dockerfile`，在镜像入口中运行 `python Heablcoin.py` 或 `cloud/task_executor.py`；用多阶段构建减小体积。  
2. **环境与密钥托管**：将 `.env` 迁移到云端的 Secrets/Config（如 K8s Secret + ConfigMap 或 ECS Secrets），只在容器启动时注入。  
3. **进程管理与调度**：使用 `systemd`/`supervisor`（虚机）或 `K8s Deployment`（容器）守护 `TaskExecutor`，设置健康检查与自动重启。  
4. **观察性**：将 `logs/` 与 `LOG_DIR` 输出重定向到云端日志（CloudWatch/ELK）；开启 `ENABLE_SMART_LOGGER`，并根据延迟调节 `PERF_SLOW_THRESHOLD_SECONDS`。  
5. **多模型路由**：在云端配置不同 provider 的密钥与 `AI_ROUTE_*`，通过 `AI_DEFAULT_PROVIDER` 控制兜底，必要时在 `cloud/api_manager.py` 中扩展自定义基座。  
6. **存储后端外接**：若要远程汇总报告/交易，补齐 `NOTION_*` 或增加对象存储/FileAdapter 的挂载卷；数据库可迁移到托管 SQLite 路径或外部 DB。  
7. **滚动升级**：先在测试环境跑 `tests/run_tests.py --quick`，再逐步替换实例；保留旧版本镜像以便快速回滚。

## 升级/验证清单
- 核对 `.env` 已填且不被提交。  
- 本地/云端都能通过 `python tests/run_tests.py --quick`。  
- SMTP 测试通过或已关闭 `EMAIL_NOTIFICATIONS_ENABLED`。  
- 观察到日志正常写入，`LOG_DIR` 可写且未爆容量。  
- 多模型路由生效：`AI_ROUTE_*` 与 `AI_DEFAULT_PROVIDER` 的组合符合预期。

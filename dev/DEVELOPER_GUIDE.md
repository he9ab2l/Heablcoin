# Heablcoin 开发者指南（云端协同版）

本目录收纳开发者必读文档与日志，便于快速上手、排障与迭代。

## 关键文件
- `dev/lessons.md`：个人交易偏好/教训，MCP `get_learning_context` 会读取并注入上下文。
- `dev/DEV_LOG.md`：开发变更、调试记录。
- `dev/DEPLOY_NOTES.md`（可创建）：部署/青龙/Redis/Notion 配置要点。
- `data/README.md`：数据分层说明（persist/tmp/ingest/reports）。

## 架构要点
- MCP 主入口：`Heablcoin.py`，注册所有工具。
- 云端哨兵：`qinglong_worker.py` + `cloud/task_manager.py` + `storage/redis_adapter.py`；任务由 `set_cloud_sentry` 写入 Redis。
- 多云 AI：`orchestration/providers.py` 支持 OpenAI/DeepSeek/Anthropic/Gemini/Groq/Moonshot/智谱 GLM，`consult_external_expert` 直连指定 provider。
- Notion 日志：`sync_session_to_notion` 依赖 `NOTION_*`。
- 数据目录：`data/` 仅存持久数据，建议使用 `data/persist/` 与 `data/tmp/` 分离，详见 `data/README.md`。

## 开发调试建议
1) 保持 `USE_TESTNET=True` 先跑 `python tests/run_tests.py unit`。  
2) Redis/青龙：设置 `REDIS_URL`，本地可先 `set_cloud_sentry` 后用 `RUN_ONCE=true python qinglong_worker.py` 验证一轮。  
3) Notion：填好 `NOTION_API_KEY`/`NOTION_DATABASE_ID`，用 `sync_session_to_notion` 测试。  
4) 多模型：在 `.env` 中只填一个 Key 也可运行；`AI_DEFAULT_PROVIDER` 控制兜底。  

## 日志与资源
- 开发日志请写入 `dev/DEV_LOG.md`。
- 资源注入：在 `dev/lessons.md` 维护最近 5 条交易教训，启动 Claude 时可通过 MCP 工具注入。
- 数据管理：参考 `data/README.md`，避免持久与临时混放。

## 待办提示
- worker 目前使用简单条件解析（price <> 阈值），如需更复杂表达式可在 `qinglong_worker._check_condition` 扩展。  
- 若需持久化监控结果到 Notion，可在 worker 中调用 `sync_session_to_notion`。  

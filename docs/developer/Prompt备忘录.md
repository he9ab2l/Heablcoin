# Prompt 备忘录（工程化规范版）

## 1. 工程化约束
1) 历史与任务：所有对话结论写入 `历史记录.json`、`任务进度.json`，使用北京时间 `YYYY-MM-DD HH:mm:ss`。
2) 架构同步：涉及分层/数据流/工具清单的改动，手工更新 `可视化系统架构.mmd`。
3) 记录格式：日志与记录文件禁止问号占位，统一 UTF-8；提交前跑 `scripts/check_naming.py` 与 `tests/run_tests.py unit`。
4) 输出风格：回答以 Markdown 数字序号为主，避免冗长口水，聚焦可执行步骤。

## 2. 对话输出模板（当用户索要“流程/方案”）
1. 目的与适用范围
2. 前置假设 / 输入要求
3. 操作步骤（1,2,3…）
4. 校验与回退
5. 风险与注意事项
6. 下一步 / 未决事项

## 3. 关键文件约定
- `历史记录.json`：`id/user_intent/details/change_type/file_path`，追加写入，不能覆盖旧记录。
- `任务进度.json`：Project/Task 双层结构，`last_updated` 用北京时间。
- `可视化系统架构.mmd`：Mermaid `graph TB`，分层节点 + 数据流。
- `lesson/`：复盘使用 `record_lesson.py` 生成，不手写时间戳。

## 4. 环境变量（核心说明）
- 交易所：`BINANCE_API_KEY` / `BINANCE_SECRET_KEY`（测试网）；默认 `EXCHANGE=binance`, `NETWORK=testnet`。
- LLM/路由：`HEABL_OPENAI_KEY`、`HEABL_DEEPSEEK_KEY`、`HEABL_GEMINI_KEY`，默认提供者 `HEABL_LLM_DEFAULT`。
- 通知：`SENDER_EMAIL`、`SENDER_PASSWORD`、`RECIPIENT_EMAIL`、`SMTP_SERVER`、`SMTP_PORT`。
- Redis/队列：`REDIS_HOST`、`REDIS_PORT`、`REDIS_PASSWORD`。
- 运行开关：`ENABLE_TASK_EXECUTOR`、`TASK_EXECUTOR_POLL_INTERVAL`、`TOOLS_DISABLED` / `TOOLS_ENABLED_ONLY`。
所有密钥均放 `.env`，提交前运行 `scripts/scan_secrets.py --staged`。

## 5. 使用者能跑通的最小指导
- 新环境：`cp .env.example .env`，填好上面的 API/SMTP/Redis；Windows 需设 `PYTHONIOENCODING=utf-8` 与 `PYTHONUTF8=1`。
- 自检：`python tests/run_tests.py unit`；如需全链路：`python tests/run_tests.py all`。
- MCP 客户端：在 Claude/Windsurf 的配置文件中指向 `python D:/MCP/Heablcoin.py`，并设置 UTF-8 环境变量。

## 6. 回答要求
- 不猜接口，先查文档/代码；不模糊执行，先确认边界。
- 优先复用现有工具，避免新造接口；改动需写测试与文档。
- 发现/修复问题必须触发 lesson 记录，命名 `lesson/问题_YYYYMMDD_HHMM.md`。

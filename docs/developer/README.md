# 开发者文档

## 推荐阅读顺序

1. `docs/developer/项目概览.md`
2. `docs/developer/架构设计.md`
3. `docs/developer/API参考.md`（MCP Tools 清单与约定）
4. `docs/developer/资源与环境变量.md`（环境变量/资源清单）
5. `docs/developer/云端模块指南.md`（API Manager / 任务发布器 / worker）
6. `docs/developer/报告系统指南.md`
7. `docs/developer/个人绩效模块指南.md`
8. `docs/developer/路线图.md`
9. `docs/developer/Prompt备忘录.md` + `docs/developer/MCP_SYSTEM_DEVELOPMENT_PROMPT_v1.0.md`
10. Runbook：`docs/developer/runbooks/多端连接集成流程标准化.md`

## 开发规范（必须遵守）

1. 历史与任务：变更要同步追加到 `历史记录.json`、更新 `任务进度.json`（北京时间 `YYYY-MM-DD HH:mm:ss`）。
2. 协议保护：MCP/JSON-RPC 使用 stdio，禁止 stdout 污染；工具必须用 `mcp_tool_safe` 做异常隔离。
3. 提交前检查：
   - `python scripts/check_naming.py`
   - `python tests/run_tests.py unit`
   - `python scripts/scan_secrets.py --staged`

## 本地验证

- 启动 MCP：`python Heablcoin.py`
- 快速回归：`python tests/run_tests.py --quick`
- 全量回归：`python tests/run_tests.py all`

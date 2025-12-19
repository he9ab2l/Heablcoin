# API 参考（MCP Tools）

本项目通过 `FastMCP` 对外暴露工具，入口为 `Heablcoin.py`，核心注册在 `src/core/server.py`（统一注册 `src/tools/*` 与 `src/skills/report/flexible_report`）。

---

## 1) 客户端接入（必读）

请优先阅读：`docs/user/MCP配置指南.md`

- Claude Desktop：配置 `claude_desktop_config.json`，`command: python`，`args: ["D:/MCP/Heablcoin.py"]`
- Windsurf：配置 `mcp_config.json`，建议带上
  - `PYTHONIOENCODING=utf-8`
  - `PYTHONUTF8=1`
- Codex CLI：`codex mcp add heablcoin --env PYTHONIOENCODING=utf-8 --env PYTHONUTF8=1 -- python d:/MCP/Heablcoin.py`

---

## 2) 工具安全与开关（必须遵守）

- MCP/JSON-RPC 通过 stdio 通信，禁止 stdout 污染；工具统一使用 `mcp_tool_safe` 做异常隔离。
- 工具软禁用（环境变量）：
  - `TOOLS_DISABLED`: 逗号分隔黑名单
  - `TOOLS_ENABLED_ONLY`: 逗号分隔白名单（非空时仅白名单生效）
- 运行时开关（管理工具）：
  - `list_tools()`
  - `set_tool_enabled(tool_name, enabled)`
  - `reset_tool_overrides()`

---

## 3) MCP Tools 清单（以 `list_tools()` / MCP `list_tools` 返回为准）

### 3.0 核心内置工具（`src/core/server.py`）

说明：这些工具直接定义在 `src/core/server.py` 中（`@mcp.tool()`），覆盖“分析/交易/通知/报告/系统状态”等基础链路。

- 通知：
  - `send_notification(title, message, msg_type="CUSTOM")`
  - `get_notification_settings()` / `set_notification_settings(...)`
- 历史与统计：
  - `get_trade_history(limit=20)` / `get_trade_statistics()`
- 市场分析（基础版）：
  - `get_market_analysis(...)` / `get_comprehensive_analysis(...)`
  - `get_market_sentiment(...)` / `get_multi_symbol_overview(...)`
  - `get_market_overview(mode="simple")` / `get_trading_signals(symbol)`
  - `get_ai_trading_advice(symbol, mode="simple")` / `get_position_recommendation(...)`
- 账户与交易：
  - `get_account_summary()` / `get_open_orders(symbol="")`
  - `place_order(...)` / `cancel_order(order_id, symbol)`
  - `calculate_position_size(...)` / `execute_strategy(symbol, strategy, amount)`
  - `get_available_strategies()`
- 报告：
  - `generate_analysis_report(...)`
- 系统/缓存/性能：
  - `get_system_status()` / `get_server_logs(lines=50)`
  - `get_cache_stats()` / `clear_cache()` / `get_performance_stats()`

### 3.1 市场分析（`src/tools/market_analysis_tools.py`）

- `get_market_analysis_modular(symbol="BTC/USDT", timeframe="1h", modules="", return_format="markdown")`（推荐：按模块组合）

### 3.2 个人绩效与复盘（`src/tools/personal_analytics_tools.py`）

- `get_personal_analysis(modules="", limit=0, initial_capital=10000.0, return_format="markdown")`
- `get_full_personal_analysis(initial_capital=10000.0, return_format="markdown")`
- `get_portfolio_analysis(return_format="markdown")`
- `get_period_performance(period="all", return_format="markdown")`
- `get_trading_session_analysis(return_format="markdown")`
- `get_cost_analysis(return_format="markdown")`
- `add_trade_journal_note(order_id, note, tags="")`
- `record_funds_flow(amount, record_type, currency="USDT", note="", date="")`
- `search_trade_history(symbol="", side="", start_date="", end_date="", limit=50)`
- `list_personal_analysis_modules()`

### 3.3 学习/训练（`src/tools/learning_tools.py`）

- `get_learning_catalog()`
- `start_learning_session(topic="risk", level="beginner")`
- `submit_learning_answer(session_id, answer, ai_enhance=False, tone="concise")`
- `get_learning_history(limit=20)`
- `get_execution_guard_settings()` / `set_execution_guard_settings(...)`
- `audit_trade_reason(...)` / `calculate_risk_reward(...)`
- `check_trend_alignment(...)` / `check_fomo(...)`
- `hunt_patterns(pattern, symbols="", timeframe="1h")`
- `get_profit_protection_advice(...)` / `analyze_loss(...)` / `simulate_what_if(...)`
- `start_blind_history_test(...)` / `reveal_blind_test(...)`
- `backtest_strategy(...)`
- `log_trade_decision(...)` / `get_trade_journal(...)`
- `record_bad_habit(...)` / `get_habit_warnings()` / `get_trader_level()` / `record_trade_result(...)`
- `calculate_volatility_size(...)`
- `check_market_events(keywords="")`
- `quick_market_overview(symbols="")`

### 3.4 AI 编排/外部专家/Notion（`src/tools/orchestration_tools.py`）

- `ai_run_pipeline(task="analysis", user_input="", context="")`
- `ai_enhance_output(content, tone="concise", context="")`
- `ai_provider_snapshot()`
- `ai_call_role(role, prompt, context="", provider="")`
- `ai_reason(prompt, context="")` / `ai_write(prompt, tone="professional")`
- `ai_remember(prompt, documents="")`
- `ai_research(query, num_sources=5)`
- `ai_critique(plan, criteria="")`
- `ai_list_roles()`
- `consult_external_expert(query, model="deepseek", context="")`
- `set_cloud_sentry(symbol, condition, action="notify", notes="")`
- `sync_session_to_notion(summary, tags="")`
- `fetch_portfolio_snapshot()`
- `get_learning_context()`

### 3.5 云端任务与 API 管理（`src/tools/cloud_tools.py`）

- Scheduler / 基础队列：
  - `start_cloud_scheduler()`
  - `publish_cloud_task(name, payload="{}", schedule_every_seconds=0, tags="")`
  - `list_cloud_tasks(status="")`
  - `cloud_scheduler_snapshot()`
  - `trigger_cloud_queue()`
- 增强队列（优先级/依赖/超时）：
  - `publish_enhanced_task(name, payload_json="{}", priority=2, timeout_seconds=60.0, depends_on="", callback_url="", notify_on_complete=True, schedule_seconds=0, tags="")`
  - `list_enhanced_tasks(status="", priority_min=0, limit=50)`
  - `get_enhanced_task_stats()`
  - `retry_failed_task(task_id)`
  - `cleanup_expired_tasks()`
- 兼容版任务（面向 MCP 调用）：
  - `publish_task(...)`
  - `get_task_status(task_id)`
  - `wait_for_task(task_id, timeout_seconds=60.0, poll_interval=1.0)`
- AI 工单模板（便于“选择模板→一键发布”）：
  - `list_task_templates(task_type="", action="")`
  - `render_task_template(template_id, overrides_json="{}")`
- Redis Pipeline（list → worker → hash）：
  - `publish_pipeline_task(query, task_id="", notify="", extra_payload_json="{}", queue_key="")`
  - `get_pipeline_result(task_id, result_hash_key="")`
  - `wait_for_pipeline_result(task_id, timeout_seconds=60.0, poll_interval=1.0, result_hash_key="")`
- API Manager：
  - `add_api_endpoint(name, base_url, api_key, model, priority=1, max_requests_per_minute=60, timeout=30.0)`
  - `get_api_manager_stats()` / `reset_api_stats()`

### 3.6 风控（`src/tools/risk_tools.py`）

- `get_risk_budget_status()`
- `record_risk_event(loss_amount, tag="", note="")`
- `update_risk_budget(period, budget, unfreeze=False)`
- `reset_risk_period(period)`
- `set_strategy_pool(name, capital, max_drawdown_pct=0.2, notes="")`
- `allocate_strategy_capital(name, amount)` / `release_strategy_capital(name, amount, realized_pnl=0.0)`
- `list_strategy_pools()`
- `suggest_vol_adjusted_notional(...)`
- `configure_circuit_breaker(symbol, threshold_pct=0.05, cooldown_minutes=30)`
- `check_circuit_breaker(symbol, move_pct, liquidity_score=1.0, reason="")`
- `circuit_breaker_status(symbol="")`

### 3.7 策略（`src/tools/strategy_tools.py`）

- `register_strategy(name, description="", tags="", enabled=True)`
- `set_strategy_enabled(name, enabled)`
- `list_strategies(filter_active=False, include_conflicts=True)`
- `record_strategy_performance(name, pnl, exposure_minutes=0.0, tags="")`
- `strategy_performance_report()`

### 3.8 治理/审计（`src/tools/governance_tools.py`）

- `score_ai_decision(decision_id, inputs_json, rationale="", tags="")`
- `recent_confidence_entries(limit=20)`
- `record_bias_sample(direction, result, pnl, market_state)`
- `bias_report()`
- `log_audit_event(event_type, severity, payload_json="", requires_ack=False)`
- `list_audit_events(limit=50)`

### 3.9 管理工具（`src/tools/admin_tools.py`）

- `list_tools()`
- `set_tool_enabled(tool_name, enabled)`
- `reset_tool_overrides()`

### 3.10 报告（`src/skills/report/flexible_report/service.py`）

- `send_flexible_report(title="综合报告", send_A=False, ..., send_I=False, **kwargs)`

---

## 4) 调试与测试

- 单元测试：`python tests/run_tests.py unit`
- 集成测试：`python tests/run_tests.py integration`
- MCP stdio 启动回归：`tests/test_mcp_stdio_startup.py`
- 日志：
  - `logs/server_debug.log`（传统日志）
  - `logs/*.jsonl`（SmartLogger 结构化日志，若启用）

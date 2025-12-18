# Heablcoin 功能总览

Heablcoin 是一个基于 MCP（Model Context Protocol）的量化交易/分析服务，支持：
- 市场分析（技术面/信号/结构等）
- AI 决策建议（新手/专业双模式）
- 自动交易与风控
- 邮件通知与报告
- 个人账户交易复盘与分析

---

## 1) 两种使用方式

- **MCP 模式（推荐）**：通过 Claude Desktop 自然语言调用工具
- **终端模式**：运行 `tests/run_tests.py` 进行自检，或在 Python 中 import 调用

---

## 2) 功能模块地图

### 2.1 市场分析（market_analysis）

- **入口工具**：`get_market_analysis(symbol, timeframe, modules, return_format)`
- **内置模块**：
  - `technical`：技术指标摘要
  - `signals`：交易信号汇总
  - `sentiment`：情绪分析（默认不启用）
  - `patterns`：K 线形态（默认不启用）
  - `structure`：市场结构（默认不启用）

### 2.2 AI 分析（Heablcoin.py 内置）

- `get_ai_trading_advice(symbol, mode)`
- `get_market_overview(mode)`
- `get_trading_signals(symbol)`
- `get_position_recommendation(symbol, account_balance, risk_tolerance)`

### 2.3 自动交易与风控

- `place_order(symbol, side, amount, price=None, order_type="market")`
- `cancel_order(order_id, symbol)`
- `execute_strategy(symbol, strategy, amount)`
- `calculate_position_size(account_balance, entry_price, stop_loss, risk_percent)`

### 2.4 报告与通知

- **灵活报告（HTML 邮件）**：`send_flexible_report(...)`
- **分析报告（保存/邮件）**：`generate_analysis_report(...)`
- **通知**：
  - `send_notification(title, message)`
  - `get_notification_settings()` / `set_notification_settings(...)`

### 2.5 个人账户交易分析（personal_analytics）

- **总览工具**：
  - `get_personal_analysis(modules, limit, initial_capital, return_format)`
  - `get_full_personal_analysis(initial_capital, return_format)`
- **子能力**：
  - 投资组合与持仓：`get_portfolio_analysis()`
  - 绩效与周期统计：`get_period_performance()`
  - 交易时段分析：`get_trading_session_analysis()`
  - 交易成本核算：`get_cost_analysis()`
  - 复盘笔记：`add_trade_journal_note(order_id, note, tags)`
  - 出入金记录：`record_funds_flow(amount, record_type, currency, note, date)`
  - 交易检索：`search_trade_history(symbol, side, start_date, end_date, limit)`

---

## 3) 数据与文件

- `trade_history.csv`
  - 用于记录成交历史（用于个人分析/复盘）
- `reports/`
  - 生成的分析报告与 meta
- `trade_journal.json`
  - 交易复盘笔记
- `funds_history.json`
  - 出入金记录

---

## 4) 安全建议

- 默认建议使用 `USE_TESTNET=True` 在测试网验证策略
- 严格配置交易限额：`MAX_TRADE_AMOUNT` / `DAILY_TRADE_LIMIT`
- 通过 `ALLOWED_SYMBOLS` 限定可交易标的

# 个人账户交易分析（personal_analytics）

本模块用于对你的**个人交易历史**进行复盘与统计，输出 Markdown/JSON 报告。

数据来源：
- `trade_history.csv`（成交记录，系统自动追加）
- `trade_journal.json`（复盘笔记，手动维护/工具写入）
- `funds_history.json`（出入金记录，手动维护/工具写入）

---

## 1) 核心能力

- **投资组合与持仓分析**：
  - 持仓数量、估值、资产分布
  - 平均持仓成本（基于成交记录估算）
  - 未实现盈亏（需要当前价格；未提供时使用成本近似）

- **交易绩效与盈亏核算**：
  - 已实现盈亏、胜率、盈亏比、盈利因子、夏普（简化）
  - 按币种/方向/星期归因
  - 周期统计：日/周/月收益

- **风险与效率指标**：
  - 最大回撤（基于闭合交易的权益曲线）
  - 连续亏损、单笔最大亏损
  - 交易频率、活跃时段（亚欧美盘）

- **交易记录与复盘工具**：
  - 交易搜索筛选
  - 复盘笔记（按订单 ID 关联）
  - 出入金记录与净值增长估算

---

## 2) MCP 工具（Claude Desktop）

### 2.1 获取分析报告

- `get_personal_analysis(modules="portfolio,performance,risk", limit=0, initial_capital=10000.0, return_format="markdown")`
- `get_full_personal_analysis(initial_capital=10000.0, return_format="markdown")`

### 2.2 常用子工具

- `get_portfolio_analysis()`
- `get_cost_analysis()`
- `get_period_performance()`
- `get_trading_session_analysis()`
- `search_trade_history(symbol="BTC", side="BUY", start_date="2025-12-01", end_date="2025-12-31")`

### 2.3 复盘与出入金

- `add_trade_journal_note(order_id="123", note="复盘内容...", tags="错误,追涨")`
- `record_funds_flow(amount=1000, record_type="deposit", note="加仓资金")`

---

## 3) 终端 / Python 直接调用

```python
from personal_analytics import PersonalAnalyzer

analyzer = PersonalAnalyzer()

# 默认模块（performance/risk/portfolio/attribution）
print(analyzer.analyze())

# 指定模块
print(analyzer.analyze(modules=["portfolio", "performance", "risk"]))

# JSON 输出
print(analyzer.analyze(return_format="json"))
```

---

## 4) 模块清单

可通过 MCP 工具 `list_personal_analysis_modules()` 查看。

常用模块：
- `portfolio`
- `performance`
- `risk`
- `attribution`
- `behavior`
- `costs`
- `periods`
- `sessions`
- `journal`
- `funds`

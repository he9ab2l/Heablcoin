# Heablcoin MCP API 规范（精简版，UTF-8）

## 快速索引

| 分类 | Tool | 说明 |
| --- | --- | --- |
| 市场 | `get_market_analysis_modular` | 多指标行情分析 |
| 账户 | `get_personal_analysis` | 个人绩效分析 |
| 学习 | `start_learning_session` | 学习对话 |
| 任务 | `publish_task` | 发布异步任务 |
| 任务 | `get_task_status` | 查询任务状态 |
| 任务 | `list_enhanced_tasks` | 查看增强队列 |
| 哨兵 | `set_cloud_sentry` | 写入 Redis 价格哨兵 |
| AI | `ai_call_role` | 按角色调用模型 |
| 研究 | `generate_quant_research_prompts` | 量化研究提示词 |
| 研究 | `run_quant_research` | 汇总研究 & 可写 Notion |
| 风控 | `get_risk_budget_status` | 查询风险预算与冻结 |
| 风控 | `record_risk_event` | 记录亏损事件 |
| 风控 | `update_risk_budget` | 修改预算/解冻 |
| 风控 | `reset_risk_period` | 重置预算周期 |
| 风控 | `set_strategy_pool` | 策略资金池初始化 |
| 风控 | `allocate_strategy_capital` | 占用策略资金 |
| 风控 | `release_strategy_capital` | 释放资金并同步盈亏 |
| 风控 | `list_strategy_pools` | 查看策略资金池 |
| 风控 | `suggest_vol_adjusted_notional` | 波动率自适应仓位 |
| 风控 | `configure_circuit_breaker` | 配置熔断阈值 |
| 风控 | `check_circuit_breaker` | 检查/记录熔断 |
| 风控 | `circuit_breaker_status` | 查看熔断状态 |
| 策略 | `register_strategy` | 策略登记/更新 |
| 策略 | `set_strategy_enabled` | 启停策略 |
| 策略 | `list_strategies` | 策略清单与冲突 |
| 策略 | `record_strategy_performance` | 策略绩效归因 |
| 策略 | `strategy_performance_report` | 策略绩效报告 |
| 治理 | `score_ai_decision` | AI 置信度计算 |
| 治理 | `recent_confidence_entries` | 置信度日志 |
| 治理 | `record_bias_sample` | 行为偏差样本 |
| 治理 | `bias_report` | 偏差诊断 |
| 审计 | `log_audit_event` | 写入审计事件 |
| 审计 | `list_audit_events` | 查询审计日志 |

---

## 任务发布 `publish_task`

**参数**
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `task_type` | str | `market_analysis/personal_analysis/...` |
| `action` | str | 自定义动作 |
| `params` | JSON str | 任务参数 |
| `priority` | int | 1~4，默认 2 |
| `timeout_seconds` | float | 超时 |
| `depends_on` | str | 依赖任务 ID（逗号分隔） |
| `callback_url` | str | 完成/失败回调 |
| `notify_on_complete` | bool | 是否发送通知 |
| `schedule_seconds` | int | 定时任务（可空） |
| `tags` | str | 标签（逗号分隔） |

**返回示例**
```json
{
  "success": true,
  "task_id": "1734567890000_1",
  "status": "pending",
  "priority": 3
}
```

## Webhook 回调
事件：`completed/failed/cancelled/expired`
```json
{
  "task_id": "...",
  "status": "completed",
  "result": {...},
  "error": null,
  "name": "market_analysis_full",
  "priority": 3,
  "updated_at": 1734567890.00
}
```

---

## 量化研究 `generate_quant_research_prompts`

**参数**
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `topic` | str | 主题，如 `BTC/USDT` |
| `focus` | str | `balanced/alpha/risk/macro` |
| `sections` | str | 可选 section id（逗号分隔） |

**返回**
```json
{
  "topic": "BTC/USDT",
  "focus": "alpha",
  "prompts": [
    {"id": "market_regime", "title": "市场状态", "prompt": "..."}
  ]
}
```

## 量化研究聚合 `run_quant_research`

**参数**
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `topic` | str | 主题 |
| `focus` | str | `balanced/alpha/risk/macro` |
| `sections` | str | 可选 section id |
| `num_sources` | int | 每个 prompt 调用次数 |
| `save_to_notion` | bool | 是否写入 Notion |
| `tags` | str | Notion 标签 |

**返回示例**
```json
{
  "topic": "BTC/USDT",
  "focus": "balanced",
  "sections": [
    {"section": "market_regime", "success": true, "content": "..."}
  ],
  "alpha_ideas": ["示例"],
  "risk_notes": ["风险提示"]
}
```

---

## 风险预算 `record_risk_event`
- 参数：`loss_amount`（正数，USDT）、`tag`、`note`
- 功能：记账亏损并更新预算，超额会自动冻结。

## 策略资金池
- `set_strategy_pool`：`name`、`capital`、`max_drawdown_pct`、`notes`
- `allocate_strategy_capital`：`name`、`amount`
- `release_strategy_capital`：`name`、`amount`、`realized_pnl`
- `list_strategy_pools`：返回 `capital/locked/available/status`

## 波动率仓位 `suggest_vol_adjusted_notional`
- 参数：`account_balance`、`risk_pct`、`symbol`、`timeframe`、`target_vol`、`lookback`
- 返回：`base_notional`、`measured_vol`、`scale`、`suggested_notional`、`note`

## 熔断控制
- `configure_circuit_breaker`：`symbol`、`threshold_pct`、`cooldown_minutes`
- `check_circuit_breaker`：`symbol`、`move_pct`、`liquidity_score`、`reason`
- `circuit_breaker_status`：可传 `symbol`

## 策略绩效
- `record_strategy_performance`：`name`、`pnl`、`exposure_minutes`、`tags`
- `strategy_performance_report`：返回贡献者/拖累者与摘要

## AI 治理
- `score_ai_decision`：`decision_id`、`inputs_json`（0~1）、`rationale`、`tags` → `score/level/action`
- `recent_confidence_entries`：`limit`
- `record_bias_sample`：`direction/result/pnl/market_state`
- `bias_report`：偏差分布与 `warnings`

## 审计
- `log_audit_event`：`event_type`、`severity`、`payload_json`、`requires_ack`
- `list_audit_events`：`limit`

---

## 参考链接
- Claude MCP SDK：https://github.com/anthropics/anthropic-sdk-python/tree/main/examples/mcp
- Claude Desktop 配置：https://github.com/anthropics/anthropic-sdk-python/tree/main/clients/claude-desktop

# MCP 任务发布示例（16 个典型场景）

> 每个场景均包含 Prompt 示例与 `publish_task` 参数，可直接复制给 AI。

---

### 1. Top10 市值查询
- Prompt：`列出当前市值最高的 10 个币种并给出 24h 涨跌幅`
- 参数：
```json
{
  "task_type": "market_analysis",
  "action": "top_market_cap",
  "params": {"limit": 10}
}
```

### 2. 鲸鱼钱包预警
```json
{
  "task_type": "data_fetch",
  "action": "whale_alert",
  "params": {"address": "0xabc...", "threshold_amount": 1000, "asset": "ETH"},
  "notify_on_complete": true
}
```

### 3. 定时定投
```json
{
  "task_type": "market_analysis",
  "action": "dca_order",
  "params": {"symbol": "ETH/USDT", "amount": 100, "frequency": "weekly"},
  "schedule_seconds": 604800
}
```

### 4. 止盈止损
```json
{
  "task_type": "personal_analysis",
  "action": "risk_guard",
  "params": {"symbol": "BTC/USDT", "take_profit": "price > 52000", "stop_loss": "price < 47000"}
}
```

### 5. 跨链套利
```json
{
  "task_type": "market_analysis",
  "action": "cross_chain_arbitrage",
  "params": {"symbol": "ARB/USDT", "chains": ["arbitrum","base"], "spread_threshold": 0.8}
}
```

### 6. Gas 优化
```json
{
  "task_type": "notification",
  "action": "gas_watch",
  "params": {"network": "Ethereum", "trigger": "price < 10"},
  "notify_on_complete": true
}
```

### 7. 新币探测
```json
{
  "task_type": "data_fetch",
  "action": "dex_liquidity_scout",
  "params": {"window_minutes": 60, "limit": 20, "sort": "liquidity_delta"},
  "priority": 3
}
```

### 8. DeFi 质押再投资
```json
{
  "task_type": "data_fetch",
  "action": "defi_yield_guard",
  "params": {"protocols": ["AAVE","Lido"], "min_apr": 5},
  "notify_on_complete": true
}
```

### 9. NFT 铸造提醒
```json
{
  "task_type": "custom",
  "action": "nft_mint_watch",
  "params": {"project": "BlueChipX", "start_time": "2025-12-20T12:00:00Z"},
  "schedule_seconds": 300
}
```

### 10. 资产归集
```json
{
  "task_type": "storage_save",
  "action": "fund_sweeper",
  "params": {"destination": "0xCOLD...", "min_balance": 50},
  "schedule_seconds": 86400
}
```

### 11. 清算预警
```json
{
  "task_type": "personal_analysis",
  "action": "liquidation_guard",
  "params": {"protocol": "AAVE", "max_ltv": 0.78},
  "notify_on_complete": true
}
```

### 12. 资金费率监控
```json
{
  "task_type": "market_analysis",
  "action": "funding_rate_watch",
  "params": {"symbol": "BTC/USDT", "threshold": 0.02}
}
```

### 13. 借贷再平衡
```json
{
  "task_type": "personal_analysis",
  "action": "borrow_rebalance",
  "params": {"protocol": "Compound", "target_ratio": 0.4}
}
```

### 14. 订单簿滑点检查
```json
{
  "task_type": "market_analysis",
  "action": "orderbook_spread",
  "params": {"symbol": "ETH/USDT", "max_spread": 0.3}
}
```

### 15. L2 跨链监控
```json
{
  "task_type": "data_fetch",
  "action": "bridge_flow_watch",
  "params": {"bridges": ["Arbitrum","Base"], "min_volume": 5000000}
}
```

### 16. 行情日报
```json
{
  "task_type": "report_generation",
  "action": "daily_market_report",
  "params": {"symbol": "BTC/USDT", "sections": ["price","sentiment","news"]},
  "notify_on_complete": true,
  "output_format": "markdown"
}
```

### 17. 量化研究提示词
```
mcp://heablcoin/generate_quant_research_prompts?topic=BTC/USDT&focus=alpha
```

### 18. 量化研究聚合
```
mcp://heablcoin/run_quant_research?topic=BTC/USDT&focus=balanced&save_to_notion=true&tags=quant,daily
```

### 19. 风险预算记录
```
mcp://heablcoin/record_risk_event?loss_amount=150&tag=manual_stop
mcp://heablcoin/get_risk_budget_status
```

### 20. 策略注册与启停
```
mcp://heablcoin/register_strategy?name=grid_guard&version=0.2&owner=deskA&symbol=ETH/USDT&timeframe=4h&direction=short&risk_level=high
mcp://heablcoin/list_strategies?include_conflicts=true
mcp://heablcoin/set_strategy_enabled?name=grid_guard&enabled=false
```

### 21. ?????????
```
mcp://heablcoin/set_strategy_pool?name=alpha&capital=15000&max_drawdown_pct=0.25
mcp://heablcoin/allocate_strategy_capital?name=alpha&amount=4000
mcp://heablcoin/list_strategy_pools
```

### 22. ?????????
```
mcp://heablcoin/suggest_vol_adjusted_notional?account_balance=20000&risk_pct=0.02&symbol=ETH/USDT&timeframe=1h&target_vol=0.02
```

### 23. ????
```
mcp://heablcoin/configure_circuit_breaker?symbol=BTC/USDT&threshold_pct=0.05&cooldown_minutes=15
mcp://heablcoin/check_circuit_breaker?symbol=BTC/USDT&move_pct=0.06&liquidity_score=0.2&reason=flash_move
```

### 24. ??????
```
mcp://heablcoin/record_strategy_performance?name=trend_alpha&pnl=380&exposure_minutes=60&tags=trend,ai
mcp://heablcoin/strategy_performance_report
```

### 25. AI ???
```
mcp://heablcoin/score_ai_decision?decision_id=rebalance-01&inputs_json={"signal_strength":0.8,"data_quality":0.9,"risk_alignment":0.7,"latency":0.6}
mcp://heablcoin/recent_confidence_entries?limit=5
```

### 26. ????
```
mcp://heablcoin/record_bias_sample?direction=long&result=win&pnl=120&market_state=trend
mcp://heablcoin/bias_report
```

### 27. ????
```
mcp://heablcoin/log_audit_event?event_type=task_publish&severity=info&payload_json={"task":"buy_breakout"}
mcp://heablcoin/list_audit_events?limit=10
```

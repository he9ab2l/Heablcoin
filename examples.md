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

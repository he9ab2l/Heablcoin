# API 参考手册 📚

本文档提供 Heablcoin MCP 服务器中所有可用工具的完整参考。

## MCP 接入速览
- Claude Desktop `claude_desktop_config.json` 示例：
```json
{
  "mcpServers": {
    "heablcoin": {
      "command": "python",
      "args": ["d:/MCP/Heablcoin.py"],
      "env": { "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1" }
    }
  }
}
```
- Windsurf `mcp_config.json` 示例同上（路径请替换为本机绝对路径）。

## 支持的 AI 提供商
通过环境变量即可启用主流模型，未配置时自动回退离线 echo：
- OpenAI 兼容：OpenAI、DeepSeek、Groq、Moonshot (Kimi)、智谱 GLM、其他兼容端点（可用 `OPENAI_BASE_URL`/`AI_DEFAULT_PROVIDER` 指向）。
- 原生：Anthropic (Claude)、Google Gemini。
- 路由：`AI_DEFAULT_PROVIDER` 决定默认，`AI_ROUTE_ANALYSIS/CRITIQUE/SYNTHESIS/SAFETY` 为多角色设置专属 provider。

---

## 工具开关与注册表

所有 MCP Tools 默认启用；支持“软禁用”（工具仍存在，但会返回禁用提示，不执行真实逻辑）。

### 环境变量

- `TOOLS_DISABLED`：黑名单，逗号分隔（例如：`TOOLS_DISABLED=place_order,cancel_order`）
- `TOOLS_ENABLED_ONLY`：白名单，逗号分隔（非空时仅白名单启用）

### 管理工具（Admin）

- `list_tools()`：列出已注册工具及启用状态（JSON）
- `set_tool_enabled(tool_name, enabled)`：运行时启用/禁用指定工具（软禁用）
- `reset_tool_overrides()`：清空所有运行时覆盖，回到环境变量/默认值

## 云端协同新工具
- `consult_external_expert(query, model="deepseek", context="")`  
  调用指定外部 AI 获取第二意见。`model` 支持 openai/deepseek/anthropic/gemini/groq/moonshot/zhipu 等。  
  示例：`consult_external_expert("BTC 技术面怎么看？", "deepseek", "{\\"timeframe\\":\\"4h\\"}")`

- `set_cloud_sentry(symbol, condition, action="notify", notes="")`  
  将监控任务写入 Redis（需 `REDIS_URL`），由青龙 `qinglong_worker.py` 轮询执行。condition 支持 `price < 1000` 等简单表达式。
  示例：`set_cloud_sentry("BTC/USDT", "price < 95000", "email_alert", "跌破支撑提醒")`

- `sync_session_to_notion(summary, tags="")`  
  将当前会话摘要写入 Notion 日志库（需 `NOTION_*`），`tags` 用逗号分隔。
  示例：`sync_session_to_notion("今日复盘：...", "daily,trade")`

- `fetch_portfolio_snapshot()`  
  返回账户资产快照（基于 `get_account_summary`）。

- `get_learning_context()`  
  读取 `dev/lessons.md` 的交易教训/偏好，用于上下文注入。

## 🤖 AI 与市场智能

### `get_ai_trading_advice`
生成 AI 驱动的交易分析和建议。

**参数**:
| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | "BTC/USDT" | 交易对 |
| `mode` | str | "simple" | 分析模式：`simple`（简单）或 `professional`（专业） |

**返回**: Markdown 格式的分析报告

**示例**:
```
get_ai_trading_advice("BTC/USDT", "simple")
get_ai_trading_advice("ETH/USDT", "professional")
```

---

### `get_market_overview`
提供加密货币市场全景概览。

**参数**:
| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `mode` | str | "simple" | `simple`（主流币概览）或 `professional`（详细板块分析） |

**返回**: Markdown 格式的市场概览

---

### `get_trading_signals`
汇总多个技术指标的信号，形成综合判断。

**参数**:
| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | "BTC/USDT" | 交易对 |

**返回**: 信号汇总（买入/卖出/中性）及置信度

---

### `get_position_recommendation`
根据风险参数计算建议仓位大小。

**参数**:
| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | "BTC/USDT" | 交易对 |
| `account_balance` | float | None | 账户总资产（可选，默认自动获取） |
| `risk_tolerance` | str | "moderate" | 风险偏好：`conservative`(1%)、`moderate`(2%)、`aggressive`(5%) |

**返回**: 建议仓位大小和杠杆

---

## 📊 市场分析

### `get_market_analysis` **(支持可视化)**
主要的技术分析工具，支持在 Claude 中生成交互式图表。

**参数**:
| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | "BTC/USDT" | 交易对 |
| `timeframe` | str | "1h" | K线周期（如 "1h", "4h", "1d"） |
| `enable_visualization` | bool | True | 是否返回可视化 JSON 数据 |

**返回**: 
- `enable_visualization=True`: JSON 字符串（用于图表渲染）
- `enable_visualization=False`: Markdown 文本报告

当 `enable_visualization=True` 时，返回的 JSON 将包含：
- `data.candles`: K 线数组（timestamp/open/high/low/close/volume）
- `data.indicators`: 指标序列（如 RSI、MACD、SMA20）
- `visualizations`: 渲染建议（如 candlestick / line）
- `summary`: 文字摘要（兜底）

---

### `get_comprehensive_analysis`
深度技术分析报告（传统工具）。

**参数**:
| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | "BTC/USDT" | 交易对 |
| `timeframe` | str | "1h" | K线周期 |

**返回**: 详尽的 Markdown 技术分析报告

---

### `get_market_sentiment`
基于价格行为和波动率分析市场情绪（恐惧与贪婪）。

**参数**:
| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | "BTC/USDT" | 交易对 |

**返回**: 情绪评分（0-100）及解读

---

### `get_multi_symbol_overview`
多币种快速概览。

**参数**: 无

**返回**: 主流币种的价格、涨跌幅、RSI 等快照

---

## 💼 账户与交易

### `get_account_summary`
获取当前钱包余额和持仓情况。

**返回**: 可用资产和已用资产明细

---

### `place_order`
在交易所执行交易下单。

**参数**:
| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | - | 交易对（必填） |
| `side` | str | - | 方向：`buy` 或 `sell`（必填） |
| `amount` | float | - | 交易数量（必填） |
| `price` | float | None | 限价单价格；为 None 时执行市价单 |
| `order_type` | str | "market" | 订单类型：`market` 或 `limit` |

**返回**: 订单执行结果

**示例**:
```
place_order("BTC/USDT", "buy", 0.001, order_type="market")
place_order("ETH/USDT", "sell", 0.1, price=4000, order_type="limit")
```

---

### `get_open_orders`
列出当前未成交的挂单。

**参数**:
| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | None | 按交易对筛选（可选） |

**返回**: 挂单列表

---

### `cancel_order`
取消指定的挂单。

**参数**:
| 参数名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `order_id` | str | 要取消的订单 ID |
| `symbol` | str | 订单的交易对 |

**返回**: 取消状态

---

### `execute_strategy`
执行指定的自动交易策略。

**参数**:
| 参数名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `symbol` | str | 交易对 |
| `strategy` | str | 策略名称（如 "ma_crossover"） |
| `amount` | float | 策略触发时的交易量 |

**返回**: 策略执行结果

---

### `get_available_strategies`
查看所有可用的交易策略。

**返回**: 策略列表及说明

---

### `calculate_position_size`
计算风控仓位大小。

**参数**:
| 参数名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `account_balance` | float | 账户余额 |
| `entry_price` | float | 入场价格 |
| `stop_loss` | float | 止损价格 |
| `risk_percent` | float | 风险比例（默认 2.0%） |

**返回**: 建议交易数量

---

## 📈 个人账户分析

基于本地交易记录 (`trade_history.csv`) 的分析工具。

### `get_personal_analysis`
通用个人绩效分析。

**参数**:
| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `modules` | str | "" | 要运行的模块，逗号分隔 |
| `limit` | int | 0 | 分析的交易数量（0=全部） |
| `initial_capital` | float | 10000.0 | 初始资金，用于计算收益率 |
| `return_format` | str | "markdown" | 输出格式：`markdown` 或 `json` |

**可用模块**:
- `performance`: 绩效分析（ROI、胜率、夏普比率）
- `risk`: 风险分析（最大回撤、连续亏损）
- `attribution`: 盈亏归因（按币种/方向/时间）
- `behavior`: 交易行为分析
- `portfolio`: 投资组合分析（持仓、浮盈）
- `costs`: 交易成本分析（手续费）
- `periods`: 周期性统计（日/周/月收益）
- `sessions`: 交易时段分析（亚欧美盘）
- `journal`: 交易复盘
- `funds`: 出入金分析

---

### `get_full_personal_analysis`
获取完整的个人交易分析报告（运行所有模块）。

**参数**:
| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `initial_capital` | float | 10000.0 | 初始资金 |
| `return_format` | str | "markdown" | 输出格式 |

---

### `add_trade_journal_note`
为特定交易添加复盘笔记。

**参数**:
| 参数名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `order_id` | str | 目标交易 ID |
| `note` | str | 笔记内容 |
| `tags` | str | 分类标签，逗号分隔（如 "fomo, 错误"） |

---

### `record_funds_flow`
记录出入金，用于调整净资产计算。

**参数**:
| 参数名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `amount` | float | 金额（正数） |
| `record_type` | str | 类型：`deposit`（入金）或 `withdraw`（出金） |
| `currency` | str | 币种，默认 USDT |
| `note` | str | 备注 |
| `date` | str | 日期（YYYY-MM-DD），留空为今天 |

---

## 🔔 系统与通知

### `get_system_status`
检查连接状态、延迟和系统健康。

**返回**: 系统状态报告

---

### `get_server_logs`
获取最近的日志条目，用于调试。

**参数**:
| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `lines` | int | 30 | 返回的日志行数 |

---

### `send_notification`
手动发送自定义邮件通知。

**参数**:
| 参数名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `title` | str | 邮件标题 |
| `message` | str | 邮件正文 |

---

### `get_notification_settings`
查看当前通知设置。

**返回**: 各类通知的开关状态

---

### `set_notification_settings`
运行时配置通知开关。

**参数**:
| 参数名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `notify_trade_execution` | bool | 交易执行通知 |
| `notify_price_alerts` | bool | 价格预警通知 |
| `notify_daily_report` | bool | 日报通知 |
| `notify_system_errors` | bool | 系统错误通知 |
| `clear_overrides` | bool | 清除所有运行时覆盖，恢复 .env 默认 |

---

## 🧾 报告生成

### `generate_analysis_report`
生成综合分析报告，可保存到本地或发送邮件。

**参数**:
| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | "BTC/USDT" | 交易对 |
| `mode` | str | "simple" | 分析模式 |
| `timeframe` | str | "1h" | K线周期 |
| `save_local` | bool | True | 是否保存到本地 `reports/` 目录 |
| `send_email_report` | bool | False | 是否发送邮件 |

---

### `send_flexible_report`
发送模块化的 HTML 邮件报告。

**参数**:
| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `title` | str | "综合报告" | 报告标题 |
| `send_A` ~ `send_I` | bool | False | 控制发送哪些模块 |

**返回**: 发送状态

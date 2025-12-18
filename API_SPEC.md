# Heablcoin MCP API 规格

## 快速索引

| 分类 | Tool | 说明 |
| --- | --- | --- |
| 市场 | `get_market_analysis_modular` | 多指标行情 |
| 账户 | `get_personal_analysis` | 绩效分析 |
| 学习 | `start_learning_session` | 学习会话 |
| 任务 | `publish_task` | 发布异步任务 |
| 任务 | `get_task_status` | 查询任务状态 |
| 任务 | `list_enhanced_tasks` | 查看增强队列 |
| 云端 | `set_cloud_sentry` | 写入 Redis 哨兵 |
| AI | `ai_call_role` | 指定角色调用模型 |

## `publish_task`

- **参数**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `task_type` | str | `market_analysis/personal_analysis/...` |
| `action` | str | 自定义动作 |
| `params` | JSON str | 任务参数 |
| `priority` | int | 1~4，默认 2 |
| `timeout_seconds` | float | 超时 |
| `depends_on` | str | 依赖任务 ID，逗号分隔 |
| `callback_url` | str | 完成/失败时回调 |
| `notify_on_complete` | bool | 是否发送通知 |
| `schedule_seconds` | int | 定时任务（可选） |
| `tags` | str | 逗号分隔标签 |

- **返回示例**
```json
{
  "success": true,
  "task_id": "1734567890000_1",
  "status": "pending",
  "priority": 3
}
```

## `get_task_status`
```json
{
  "success": true,
  "task": {
    "task_id": "...",
    "status": "completed",
    "result": {"output": {...}},
    "callback_attempts": 1,
    "callback_error": null
  }
}
```

## Webhook 回调
- 触发状态：`completed/failed/cancelled/expired`
- Payload：
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

## 其他常用 Tool

| Tool | 功能要点 |
| --- | --- |
| `publish_cloud_task` | 简单任务（文件持久化） |
| `publish_enhanced_task` | 低阶增强版接口 |
| `start_cloud_scheduler` | 启动本地定时器 |
| `consult_external_expert` | 多云模型复核 |
| `get_market_analysis_modular` | modules=`trend,volatility,signals` |

更多请见 `docs/user/MCP配置指南.md` 与 `docs/developer/README.md`。

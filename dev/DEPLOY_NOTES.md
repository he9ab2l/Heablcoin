# 部署与运维要点（青龙/Redis/Notion）

## 环境变量速查
- Redis：`REDIS_URL`（必填），`REDIS_SSL`（可选），`REDIS_MONITOR_QUEUE_KEY`（可选，默认 heablcoin:monitor_queue）。
- 青龙 worker：`RUN_ONCE`（默认 true，青龙设为 false 持续轮询），`WORKER_INTERVAL`（秒）。
- Notion：`NOTION_API_KEY`，`NOTION_DATABASE_ID`（或 `NOTION_REPORTS_DB_ID`/`NOTION_TRADES_DB_ID`）。
- 邮件：`EMAIL_NOTIFICATIONS_ENABLED` + SMTP 相关。
- Pipeline worker（Tavily→DeepSeek→多通道通知）：
  - `TASK_QUEUE_KEY`（默认 mcp:tasks）
  - `RESULT_HASH_KEY`（默认 mcp:results）
  - `HEABL_TAVILY_KEY`（必填）
  - `HEABL_DEEPSEEK_KEY`（必填），`HEABL_DEEPSEEK_MODEL`（默认 deepseek-chat）
  - `SERVERCHAN_SENDKEY`（Server酱，选填）
  - `FEISHU_WEBHOOK`（飞书 Webhook，选填）、`FEISHU_SECRET`（可选签名）
  - `NOTIFY_DEFAULT`（默认 serverchan，逗号分隔），`NOTIFY_FAILOVER`（默认 serverchan）

## 青龙部署简要
1) 仅上传 `qinglong_worker.py`（哨兵）或 `cloud/pipeline_worker.py`（搜索/总结/推送），加上依赖文件 `cloud/task_manager.py`、`storage/redis_adapter.py`。  
2) 任务命令示例：`cd /ql/data/heablcoin && RUN_ONCE=false WORKER_INTERVAL=60 python qinglong_worker.py`。  
   Pipeline 示例：`cd /ql/data/heablcoin && RUN_ONCE=false python cloud/pipeline_worker.py`。  
3) 确保依赖安装：`pip install redis ccxt pandas requests`（按需）。  

## Redis 检查
- 本地验证：`set_cloud_sentry` 写入后，`RUN_ONCE=true python qinglong_worker.py` 跑一轮；查看输出。  
- SSL：如用云 Redis，设置 `REDIS_SSL=true`。  

## Notion 检查
- 环境填好 `NOTION_*`，调用 MCP 工具 `sync_session_to_notion` 写入一条日志。  
- 页面/数据库权限需允许集成写入。  

## 日志
- Worker 输出可重定向到青龙日志；需要持久记录可调用 `sync_session_to_notion`。  

## 测试 task 示例（LPUSH 到任务队列）
```json
{"id":"t1","payload":{"query":"BTC 走势怎么看？","notify":["serverchan"]}}
{"id":"t2","payload":{"query":"ETH 技术面","notify":["feishu"]}}
{"id":"t3","payload":{"query":"SOL 支撑压力","notify":["serverchan","feishu"]}}
```

验证步骤（最小 5 步）
1) 设置环境变量：`REDIS_URL`、Tavily/DeepSeek Key、通知通道（SERVERCHAN_SENDKEY 或 FEISHU_WEBHOOK）。  
2) 将上述 JSON 逐条 `LPUSH mcp:tasks '...json...'`。  
3) 在青龙运行：`RUN_ONCE=false python cloud/pipeline_worker.py`（或手动单次 `RUN_ONCE=true`）。  
4) 检查通知：对应的微信/飞书群是否收到消息。  
5) Redis `hget mcp:results t1` 查看 `search_results/summary/notify_status` 是否完整。  

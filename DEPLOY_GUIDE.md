# 部署与运维指南

## 1. 快速脚本

| 场景 | 命令 |
| --- | --- |
| 初始化服务器依赖 | `sudo bash scripts/setup.sh` |
| 拉取更新 + 测试 + PM2 守护 | `APP_DIR=/opt/heablcoin bash scripts/deploy.sh` |

> `setup.sh` 安装 Python/Node/Redis/pm2；`deploy.sh` 默认使用 `.venv` 与 `pm2` 守护 `Heablcoin.py`。

## 2. 本地开发
1. `cp .env.example .env`，填入 Binance/Redis/API Key（建议 Testnet）。
2. `pip install -r requirements.txt`
3. `python tests/run_tests.py unit`
4. `python Heablcoin.py` 验证 MCP 客户端能连通。

## 3. 服务器部署
1. 准备 `/opt/heablcoin`，`git clone` 仓库。
2. 运行 `scripts/setup.sh`（或参照脚本手动执行 apt/pip 安装）。
3. 运行 `scripts/deploy.sh`，PM2 会注册 `heablcoin-mcp`。
4. `pm2 log heablcoin-mcp` 查看日志；`pm2 save` 持久化。

## 4. Redis & 任务队列
- `.env` 配置 `REDIS_URL`（或 host/pass），默认端口 6379。
- `TaskExecutor` 根据 `ENABLE_TASK_EXECUTOR` 自动启动，轮询 `data/enhanced_cloud_tasks.json`。
- `publish_task` 支持 `callback_url`；Redis 任务可由青龙 worker (`qinglong_worker.py`) 消费。

## 5. Nginx / SSL / MCP Inspector
```nginx
server {
    listen 443 ssl;
    server_name mcp.example.com;
    ssl_certificate     /etc/letsencrypt/live/mcp/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mcp/privkey.pem;
    location / {
        proxy_pass http://127.0.0.1:3333;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
- MCP Inspector: `npx @modelcontextprotocol/inspector --server-command "python Heablcoin.py"`，建议仅暴露内网或 VPN。

## 6. Webhook / 安全
- 设置 `.env` 中的 `TASK_WEBHOOK_SECRET`，回调端可校验 `X-Heabl-Signature`。
- 推荐使用 HTTPS，必要时限制源 IP。

## 7. 故障排查
- `codex` 连接超时：确保 `PYTHONUTF8=1`，stdout 无多余 print。
- 任务不执行：检查 `data/enhanced_cloud_tasks.json` 状态是否卡在 pending，或 `pm2 log` 是否有异常。
- 回调失败：`get_task_status` 中查看 `callback_error` 字段。

## 8. 运维建议
- CI：GitHub Actions 调用 `python tests/run_tests.py all`。
- 提交：使用 `./gp.sh "feat: ..."`, 自动扫描敏感信息。
- 监控：Nginx + Prometheus/Vector 采集 `logs/*.log`，Redis 使用 `redis-cli monitor`。

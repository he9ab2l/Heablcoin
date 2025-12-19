# Heablcoin MCP Trading System

[English](README.md) | [中文](README.zh-CN.md)

> Intelligent, modular crypto trading assistant compliant with the Model Context Protocol (MCP).

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)

Heablcoin is a modular trading system built for MCP clients (Claude Desktop, Windsurf). It provides market analysis, trading execution, reporting, and personal performance tracking with safety-first defaults.

## Key Features

- AI & analysis: multi-mode market analysis (technical/sentiment/signals) via natural language.
- Visualization: structured JSON output for interactive charts.
- Trading & portfolio: safe execution with whitelists, limits, and position sizing.
- Notifications: configurable email alerts for trades, prices, and daily reports.
- Task publishing: describe conditional trades via `publish_task`, run asynchronously with webhook callbacks.
- Quant research: curated `ai_research` prompt kit + aggregator with optional Notion logging.
- Risk layering: account budgets, per-strategy capital pools, volatility-aware sizing, and exchange-level circuit breakers.
- Governance & audit: strategy registry + attribution, AI confidence scoring, bias diagnosis, and append-only audit trail.
- Extensibility: exchange adapter, Redis-backed queues, and pluggable notifier framework.

## Architecture at a Glance

- Entry & MCP server: `Heablcoin.py` (MCP stdio), core runtime in `src/core/server.py`.
- Tools & skills: MCP tools under `src/tools`, higher-level skills in `src/skills` (market analysis, personal analytics, research, strategy/risk/governance).
- Execution & queues: Redis-backed schedulers/workers in `src/core/cloud` for async publish/execute and webhooks.
- Storage adapters: file/Redis/Notion/email adapters in `src/storage`; configuration helpers in `src/utils/env_helpers.py`.
- Safety & governance: `src/skills/risk`, `src/skills/governance`, `src/core/mcp_safety.py` enforce budgets, circuit breakers, confidence checks, audit trail.
- Data & logs: persisted JSON under `data/`, logs under `logs/`, lessons under `lesson/` for incident learnings.

## Quick Links

- [Quick Start](docs/user/快速开始.md)
- [Installation Guide](docs/user/安装指南.md)
- [Configuration Guide](docs/user/配置指南.md)
- [MCP Configuration](docs/user/MCP配置指南.md)
- [API Reference](docs/developer/API参考.md)
- [API Spec (Tools & Payloads)](API_SPEC.md)
- [Deployment Guide](DEPLOY_GUIDE.md)
- [Architecture](docs/developer/架构设计.md)
- [Task Examples](examples.md)

## Environment Variables (core)

Set via `.env` (copy from `.env.example`). Keep secrets private.

| Name | Purpose | Notes |
| --- | --- | --- |
| `HEABL_ENV` | Environment: `dev` / `prod` | Controls logging/detail level |
| `HEABL_MODE` | Mode: `paper` / `live` | Default paper; do not use live without approval |
| `EXCHANGE` | Exchange name | e.g., `binance` |
| `NETWORK` | Network | e.g., `testnet` |
| `BINANCE_API_KEY` / `BINANCE_SECRET_KEY` | API credentials | Use testnet keys first |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_PASSWORD` | Redis queue/cache | Required for async tasks |
| `SENDER_EMAIL` / `SENDER_PASSWORD` / `SMTP_SERVER` / `SMTP_PORT` / `RECEIVER_EMAIL` | Email alerts | Optional; enables notifier tests |
| `NOTION_API_KEY` / `REPORTS_DB_ID` | Notion logging | Optional for research/report sync |
| LLM keys (`HEABL_OPENAI_KEY`, `HEABL_DEEPSEEK_KEY`, etc.) | Multi-provider routing | Optional; configure what you own |

## Setup

```bash
# 1) Clone
git clone https://github.com/your/repo.git heablcoin
cd heablcoin

# 2) Configure
cp .env.example .env
# edit .env with keys (use testnet/paper mode first)

# 3) Install
pip install -r requirements.txt

# 4) Verify
python tests/run_tests.py unit
```

## MCP Usage

### Claude Desktop
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "heablcoin": {
      "command": "python",
      "args": ["/absolute/path/to/your/Heablcoin.py"]
    }
  }
}
```
Then ask: ?Analyze BTC price action? or ?Check my account balance?.

### Windsurf (Codeium MCP)
`mcp_config.json`:
```json
{
  "mcpServers": {
    "heablcoin": {
      "args": ["/absolute/path/to/your/Heablcoin.py"],
      "command": "python",
      "disabled": false,
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

### Terminal Smoke Tests
```bash
python Heablcoin-test.py --quick
python tests/run_tests.py unit
python -c "from core.cloud.task_executor import submit_task; submit_task('market_analysis','top_market_cap',{'limit':5})"
```
Email check (may send real email):
```bash
python tests/run_tests.py email
```

## Task Publishing & Async Queue

- Publish conditional tasks via `publish_task`/`publish_enhanced_task`; workers in `src/core/cloud` pick them up and notify via webhook.
- Example (MCP call syntax):
  - `mcp://heablcoin/publish_task?name=buy_the_dip&payload_json={"symbol":"BTC/USDT","when_price_lt":42000,"notional":200}`
  - `mcp://heablcoin/publish_enhanced_task?name=rebalance&priority=5&payload_json={"strategy":"alloc","target_pct":0.2}`
- Status tracking: `Pending ? Executing ? Completed/Failed`, persisted in `data/tasks/`.

## What You Get Out-of-the-Box

- **Market analysis**: technical/sentiment/trend/structure quality, flow pressure, volatility & signals; JSON for charts.
- **Trading & portfolio**: exchange adapter, position sizing, profit protection, portfolio breakdown.
- **Research kit**: multi-LLM prompt sets, news/research aggregation, optional Notion logging.
- **Risk & governance**: risk budgets (daily/weekly/monthly), per-strategy pools, vol-adjusted sizing, circuit breakers, strategy registry, attribution, AI confidence/bias/audit trail.
- **Reporting**: flexible reports, cost analysis, personal analytics with time/market/session slices.
- **Notifications**: email (and webhook-ready) for tasks, price, daily digest.

## Development Workflow

```bash
# Lint / format (optional hooks)
python scripts/scan_secrets.py --staged

# Run unit tests
python tests/run_tests.py unit
# Run integration tests
python tests/run_tests.py integration
# Run full suite
python tests/run_tests.py all

# Dev server (MCP stdio)
python Heablcoin.py
```
Guides: `dev/DEVELOPER_GUIDE.md`, `dev/DEV_LOG.md`, `docs/developer/Prompt备忘录.md` (response rules & conventions).

## Logs, Data, and Persistence

- Logs: `logs/` (analysis, performance, server_debug). Lesson logs in `lesson/` (postmortems).
- Data: JSON under `data/` (risk budgets, strategy registry, circuit breakers, AI governance, tasks).
- Reports: `reports/` (if enabled), Notion sync if `NOTION_API_KEY` configured.

## Safety & Governance Toggles

- Run in `HEABL_MODE=paper` + `NETWORK=testnet` by default.
- Risk budgets and circuit breakers will freeze execution on breach; check `mcp://heablcoin/get_risk_budget_status`.
- Strategy conflicts and AI confidence checks surface before acting; most tools return warnings instead of executing when signals are weak.

## License
This project is licensed under the [MIT License](LICENSE).

---
Disclaimer: This software is for educational and research purposes only. Trading cryptocurrencies involves significant risk. Use at your own risk.

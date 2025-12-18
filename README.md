# Heablcoin MCP Trading System

[English](README.md) | [简体中文](README.zh-CN.md)

> Intelligent, modular crypto trading assistant compliant with the Model Context Protocol (MCP).

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

Heablcoin is a modular trading system built for MCP clients (Claude Desktop, Windsurf). It provides market analysis, trading execution, reporting, and personal performance tracking with safety-first defaults.

## Key Features

- AI & analysis: multi-mode market analysis (technical/sentiment/signals) via natural language.
- Visualization: structured JSON output for interactive charts.
- Trading & portfolio: safe execution with whitelists, limits, and position sizing.
- Notifications: configurable email alerts for trades, prices, and daily reports.
- Extensibility: exchange adapter and pluggable notifier framework.

## Quick Links

- [Installation Guide](docs/user/安装指南.md)
- [Configuration Guide](docs/user/配置指南.md)
- [API Reference](docs/developer/API参考.md)
- [Architecture](docs/developer/架构设计.md)

## Installation Summary

```bash
# 1. Clone
git clone https://github.com/your/repo.git heablcoin
cd heablcoin

# 2. Configure
cp .env.example .env
# Edit .env with Binance API keys (use testnet first)

# 3. Install
pip install -r requirements.txt

# 4. Verify
python tests/run_tests.py --quick
```

## Usage

### Claude Desktop (MCP)
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "heablcoin": {
      "command": "python",
      "args": ["D:/MCP/Heablcoin.py"]
    }
  }
}
```
Then ask: “Analyze BTC price action” or “Check my account balance”.

### Windsurf (Codeium MCP)
Configure `mcp_config.json`:
```json
{
  "mcpServers": {
    "heablcoin": {
      "args": ["d:/MCP/Heablcoin.py"],
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

### Terminal Self-Check
```bash
python Heablcoin-test.py --quick
python tests/run_tests.py unit
```

Email configuration test (optional, may send a real email):
```bash
python tests/run_tests.py email
```

## License
This project is licensed under the [MIT License](LICENSE).

---
Disclaimer: This software is for educational and research purposes only. Trading cryptocurrencies involves significant risk. Use at your own risk.
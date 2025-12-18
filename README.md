# Heablcoin 🪙

[English](README.md) | [简体中文](README.zh-CN.md)

> **Intelligent Agentic Trading System compliant with the Model Context Protocol (MCP)**

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

Heablcoin is a powerful, modular crypto trading assistant designed to work seamlessly with LLMs like Claude via the Model Context Protocol (MCP). It provides comprehensive market analysis, automated trading execution, and detailed personal performance tracking.

## ✨ Key Features

*   **🤖 AI & Analysis**: Multi-mode market analysis (Technical, Sentiment, Signals) powered by standard libraries and accessible via natural language.
*   **📊 Visualization**: Interactive chart generation within Claude Desktop.
*   **💼 Portfolio Management**: Robust ledger system to track PnL, risk, and attribution.
*   **🔔 Smart Notifications**: Configurable email alerts for trades, prices, and daily reports.
*   **🛡️ Risk Control & Position Sizing**: Built‑in limits, whitelists, and safe‑mode defaults. New risk management utilities provide automatic position sizing based on account balance and stop‑loss distance, along with trailing stop helpers to lock in gains.

*   **⚙️ Multi-Exchange Support**: Unified `ExchangeAdapter` with native Binance implementation and stubs for OKX and Bybit to simplify future expansion.
*   **📈 Backtesting Engine (Basic)**: New `run_backtest` function allows quick evaluation of strategy logic offline without external dependencies.
*   **🔔 Multi‑Channel Notifications**: Pluggable `Notifier` with console and Telegram channels out‑of‑the‑box, extensible to other messaging platforms.

## 🚀 Quick Links

*   [**Installation Guide**](docs/user/安装指南.md)
*   [**Configuration Guide**](docs/user/配置指南.md)
*   [**API Reference**](docs/developer/API参考.md)
*   [**Architecture**](docs/developer/架构设计.md)

## 📦 Installation Summary

```bash
# 1. Clone
git clone https://github.com/your/repo.git heablcoin
cd heablcoin

# 2. API Setup
cp .env.example .env
# Edit .env with your Binance API Key

# 3. Install
pip install -r requirements.txt

# Optional: enable Telegram notifications
# python -m pip install --break-system-packages python-telegram-bot

# 4. Verify
python tests/run_tests.py --quick
```

## Usage

### With Claude Desktop (MCP)
Add the server to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "heablcoin": {
      "command": "python",
      "args": ["/absolute/path/to/heablcoin/Heablcoin.py"]
    }
  }
}
```
Then ask Claude: *"Analyze BTC price action"* or *"Check my account balance"*.

### With Windsurf (Codeium MCP)
Configure your `mcp_config.json` with an absolute path:

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

### From Terminal
Use the built-in test harness:
```bash
python tests/run_tests.py unit
```

Email configuration test (optional, may send a real email):

```bash
python tests/run_tests.py email
```

## License
This project is licensed under the [MIT License](LICENSE).

---
*Disclaimer: This software is for educational and research purposes only. Trading cryptocurrencies involves significant risk. Use at your own risk.*
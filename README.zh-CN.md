# Heablcoin 🪙

[English](README.md) | [简体中文](README.zh-CN.md)

> **符合 Model Context Protocol (MCP) 的智能交易助手（可在 Claude Desktop / Windsurf 中使用）**

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

Heablcoin 是一个面向 LLM（如 Claude）的模块化加密货币交易/分析助手，通过 MCP 协议提供市场分析、交易执行、通知与个人绩效追踪能力。

## ✨ 核心特性

- **AI & 分析**：多模式市场分析（技术面/情绪/信号），可用自然语言触发
- **可视化**：在 Claude Desktop 内生成交互式图表（基于结构化 JSON 输出）
- **账户与交易**：查询资产、执行下单（受风控约束）
- **智能通知**：交易/价格/报告邮件通知（可细粒度开关）
- **风控保护与仓位管理**：限额、白名单、测试网默认等安全机制，并新增仓位管理工具可根据账户余额和止损距离自动计算仓位，提供追踪止损帮助锁定收益。

 - **多交易所支持**：全新的 `ExchangeAdapter` 抽象，提供 Binance 实现以及 OKX/Bybit 桩代码，方便未来扩展。
 - **基础回测引擎**：通过 `run_backtest` 快速验证策略逻辑，无需额外依赖。
 - **多通道通知**：引入 `Notifier` 框架，支持控制台、Telegram 等扩展通知渠道。

## 🔗 快速链接

- [安装指南](docs/user/安装指南.md)
- [配置指南（.env）](docs/user/配置指南.md)
- [API 参考](docs/developer/API参考.md)
- [架构设计](docs/developer/架构设计.md)

## 📦 安装摘要

```bash
# 1. 克隆
git clone https://github.com/your/repo.git heablcoin
cd heablcoin

# 2. 配置
cp .env.example .env
# 编辑 .env，填入 Binance API Key / Secret 等

# 3. 安装依赖
pip install -r requirements.txt

# 可选：启用 Telegram 通知
# python -m pip install python-telegram-bot

# 4. 快速自检
python tests/run_tests.py --quick
```

## 🧩 使用方式

### 方式 1：Claude Desktop（MCP）

在 `claude_desktop_config.json` 中添加：

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

然后在 Claude 中直接提问：
- “分析 BTC 走势并画图”
- “查看我的账户余额”

更多细节见：[docs/user/MCP使用指南.md](docs/user/MCP使用指南.md)

### 方式 2：Windsurf（Codeium MCP）

在 `mcp_config.json` 中添加（示例）：

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

### 方式 3：终端自检/测试

```bash
# 单元测试
python tests/run_tests.py unit

# 集成测试
python tests/run_tests.py integration

# 全量测试
python tests/run_tests.py all
```

邮箱配置测试（可选，会尝试真实发送邮件）：

```bash
python tests/run_tests.py email
```

## 📄 License

本项目使用 [MIT License](LICENSE)。

---

*免责声明：本软件仅供学习与研究用途。加密货币交易风险极高，盈亏自负。*

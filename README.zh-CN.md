# Heablcoin MCP 交易系统

[English](README.md) | [简体中文](README.zh-CN.md)

> 符合 Model Context Protocol (MCP) 的智能交易助手。

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

Heablcoin 是一个面向 MCP 客户端（Claude Desktop、Windsurf）的模块化交易系统，提供市场分析、交易执行、报告与个人绩效追踪，并默认启用安全约束。

## 核心特性

- AI 分析：技术面/情绪/信号多模式分析，可直接用自然语言触发。
- 可视化：结构化 JSON 输出，支持交互式图表。
- 交易与账户：白名单、限额、仓位计算等安全机制。
- 通知系统：交易/价格/日报邮件通知，细粒度开关控制。
- 可扩展性：交易所适配器与可插拔通知框架。

## 快速链接

- [安装指南](docs/user/安装指南.md)
- [配置指南（.env）](docs/user/配置指南.md)
- [API 参考](docs/developer/API参考.md)
- [架构设计](docs/developer/架构设计.md)

## 安装摘要

```bash
# 1. 克隆

git clone https://github.com/your/repo.git heablcoin
cd heablcoin

# 2. 配置
cp .env.example .env
# 编辑 .env，先使用测试网

# 3. 安装依赖
pip install -r requirements.txt

# 4. 快速自检
python tests/run_tests.py --quick
```

## 使用方式

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
然后在 Claude 中提问：
- “分析 BTC 走势并画图”
- “查看我的账户余额”

### 方式 2：Windsurf（Codeium MCP）
在 `mcp_config.json` 中添加：
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
python Heablcoin-test.py --quick
python tests/run_tests.py unit
```

邮箱配置测试（可选，会尝试真实发送邮件）：
```bash
python tests/run_tests.py email
```

## License
本项目使用 [MIT License](LICENSE)。

---
免责声明：本软件仅供学习与研究用途。加密货币交易风险极高，盈亏自负。
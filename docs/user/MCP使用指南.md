# Heablcoin MCP 使用指南

## 📋 概述

MCP 模式用于在 **Claude Desktop** 中通过自然语言对话调用 Heablcoin 的工具（`@mcp.tool()`），适合日常使用与交互式分析。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env`（可复制 `.env.example`）：

- `BINANCE_API_KEY`
- `BINANCE_SECRET_KEY`
- `USE_TESTNET=True`（推荐先用测试网）

可选邮件通知：

- `EMAIL_NOTIFICATIONS_ENABLED=True`
- `SENDER_EMAIL`
- `SENDER_PASSWORD`
- `RECEIVER_EMAIL`
- `SMTP_SERVER`
- `SMTP_PORT`

### 3. 配置 Claude Desktop

编辑 `claude_desktop_config.json`，添加：

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

#### Claude Desktop 配置文件位置（Windows）

通常在：

```text
%APPDATA%\Claude\claude_desktop_config.json
```

如果你不确定位置，可以在 Claude Desktop 的设置里找到 MCP/Servers 配置入口。

---

### 3.1 配置 Windsurf（Codeium）

你的 Windsurf MCP 配置类似于：

```json
{
  "mcpServers": {
    "heablcoin": {
      "args": [
        "d:/MCP/Heablcoin.py"
      ],
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

关键点：
- `args` 使用 **绝对路径** 指向 `Heablcoin.py`
- 建议保留 `PYTHONUTF8/PYTHONIOENCODING`，避免中文输出编码问题

### 4. 重启 Claude Desktop

完全退出并重启 Claude Desktop 后，在对话中提问，例如：

- “帮我分析下 BTC 现在能不能买入”
- “给我一份 ETH 的专业分析报告”

---

## 常用能力与提示词示例

### AI 分析

- “分析 BTC，简单模式”
- “分析 ETH，专业模式”

### 市场概览

- “市场全景（简单）”
- “主流币种快速概览”

### 交易与风控

- “我有 10000U，稳健风格，BTC 建议仓位？”
- “市价买入 0.001 BTC（测试网）”

### 报告生成（可保存/可邮件）

- “生成 BTC 简单模式报告并保存到本地”
- “生成 BTC 专业报告并发送到邮箱”

### 个人账户交易分析（复盘/绩效/风险）

- “给我一份个人交易分析报告”
- “只看我的持仓和浮动盈亏”
- “统计我最近 30 天的收益情况”
- “帮我按币种做盈亏归因”
- “给订单 123456 添加复盘笔记：这次追涨失败，应该等待回调”
- “记录一笔入金：1000 USDT，备注：加仓资金”

### 灵活邮件报告（HTML 模块化）

- “发送综合报告到邮箱（默认全模块）”
- “只发送模块 A 和 B 的报告”

---

## 输出与文件

### 日志

- 默认日志文件：`logs/server_debug.log`
- 可通过 `.env` 配置：
  - `LOG_LEVEL=INFO`
  - `LOG_FILE=logs/server_debug.log`

### 报告

- 分析报告目录：`reports/analysis_reports/YYYYMMDD/`
- 文件命名：`YYYYMMDD_HHMMSS__SYMBOL__MODE__TIMEFRAME.md`
- 元数据：同名 `.meta.json`

灵活邮件报告（HTML）备份目录：
- `reports/flexible_report/YYYYMMDD/`

用户查询备份目录：
- `reports/query_backups/YYYYMMDD/`

---

## 验证步骤

1. 先在终端运行：

```bash
python tests/run_tests.py --quick
```

### 邮箱配置验证（可选）

邮箱测试会尝试真实连接 SMTP 并发送一封测试邮件：

```bash
python tests/run_tests.py email
```

或直接运行单文件：

```bash
python tests/test_email_connection.py
```

2. 确认 Claude Desktop 中能看到工具列表，并能成功调用。

---

## 更多文档

- [文档索引](README.md)

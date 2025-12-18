# Heablcoin 终端使用指南

## 概述

终端模式允许你**无需 MCP 客户端**，直接在命令行中测试和使用 Heablcoin 的所有功能。适合：
- 快速测试功能
- 脚本自动化
- 开发调试
- 批量数据分析

**优势**:
- 无需 Claude Desktop
- 可编程脚本化
- 直接查看原始输出
- 适合自动化任务

---

## 快速开始

### 1. 环境准备

确保已安装依赖：
```bash
pip install -r requirements.txt
```

确保已配置 `.env` 文件（参考 `.env.example`）

### 2. 运行测试工具

Heablcoin 提供了专门的终端测试入口：`tests/run_tests.py`（推荐）

**快速测试**（推荐新手）:
```bash
python tests/run_tests.py --quick
```
耗时约 2 分钟，测试：
- 交易所连接
- 系统状态
- 市场分析
- AI 分析功能

**仅测试 AI 功能**:
```bash
python tests/run_tests.py unit
```

**完整测试**:
```bash
python tests/run_tests.py all
```
耗时约 5 分钟，测试所有功能

**包含实际下单测试**（测试网）:
```bash
python tests/run_tests.py integration
```

---

## 直接调用功能

### 方式 1: Python 交互式

```python
# 启动 Python
python

# 导入功能
from Heablcoin import (
    get_ai_trading_advice,
    get_market_overview,
    get_account_summary,
    get_trading_signals,
    place_order
)

# 使用功能
print(get_ai_trading_advice("BTC/USDT", "simple"))
print(get_market_overview("simple"))
print(get_account_summary())
```

### 方式 2: 编写自定义脚本

创建 `my_script.py`：

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from Heablcoin import *

# 获取 AI 建议
def get_btc_advice():
    result = get_ai_trading_advice("BTC/USDT", "professional")
    print(result)

# 检查账户
def check_balance():
    result = get_account_summary()
    print(result)

# 自动交易逻辑
def auto_trade():
    # 获取市场信号
    signals = get_trading_signals("BTC/USDT")
    print(signals)
    
    # 根据信号决策
    if "买入" in signals:
        # 计算仓位
        position = get_position_recommendation("BTC/USDT", None, "moderate")
        print(position)
        
        # 下单（示例）
        # result = place_order("BTC/USDT", "buy", 0.001, order_type="market")
        # print(result)

if __name__ == "__main__":
    get_btc_advice()
    check_balance()
    # auto_trade()  # 取消注释以启用自动交易
```

运行：
```bash
python my_script.py
```

---

## 个人账户交易分析（personal_analytics）

个人交易分析基于 `trade_history.csv`（以及可选的 `trade_journal.json` / `funds_history.json`）生成复盘与统计报告。

```python
from personal_analytics import PersonalAnalyzer

analyzer = PersonalAnalyzer()

# 默认模块（performance/risk/portfolio/attribution）
print(analyzer.analyze())

# 指定模块
print(analyzer.analyze(modules=["portfolio", "performance", "risk"]))

# 输出 JSON
print(analyzer.analyze(return_format="json"))
```

---

## 相关文档

- [MCP 使用指南](USAGE_MCP.md) - 在 Claude Desktop 中使用
- [API 参考文档](api_reference.md) - 完整 API 说明
- [故障排查指南](troubleshooting.md) - 问题解决方案
- [文档索引](INDEX.md) - 全部文档入口

---

**提示**：终端模式非常适合开发和调试，但对于日常交易，推荐使用 MCP 模式以获得更好的对话体验。

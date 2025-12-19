# Claude / Windsurf MCP 导入与验收清单

本文档用于把 Heablcoin MCP Server 导入 Claude Desktop 与 Windsurf，并对常见场景 + 边界情况做可复用验收。

## 1. 前置条件

- 你已完成 `.env` 配置（所有变量参数已配置好）
- 本地已通过：`python tests/run_tests.py unit` 与 `python tests/run_tests.py integration`
- MCP Server 启动入口：`Heablcoin.py`

## 2. Claude Desktop 导入

在 `claude_desktop_config.json` 中添加（示例，按你的实际路径修改）：

```json
{
  "mcpServers": {
    "heablcoin": {
      "command": "python",
      "args": ["D:/MCP/Heablcoin.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

验收：
- Claude Desktop 能看到 server 已连接
- 执行任意 tool 不出现 JSON 解析错误

## 3. Windsurf 导入

在 `mcp_config.json` 中添加（示例，按你的实际路径修改）：

```json
{
  "mcpServers": {
    "heablcoin": {
      "command": "python",
      "args": ["D:/MCP/Heablcoin.py"],
      "disabled": false,
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

验收：
- Windsurf MCP 列表中显示 server 正常
- 执行 tool 后，响应稳定且无 stdout 污染导致的断链

## 4. 场景化验收用例（建议顺序）

### 4.1 基础连通（P0）

- 目标：确认 MCP 可用、工具可调用、输出可解析。

用例：
- 让助手执行一个“只读、无外部依赖”的分析类工具（若工具需要 symbol，则用 BTC/ETH 等）

验收：
- 返回成功
- 无 `Invalid JSON`、无崩溃

### 4.2 错误参数边界（P0）

用例：
- 传入不合法 `symbol`（空字符串/超长/包含非法字符）
- 传入不合法 `timeframe`
- 传入极端数值（负数、超大 limit）

验收：
- 返回可理解错误提示
- 服务端不崩溃、不死锁

### 4.3 外部依赖不可用（P1）

用例：
- Redis 不可用（或临时关闭）时执行依赖队列的工具
- Notion 未配置时执行 notion 同步相关工具

验收：
- 明确提示“依赖未配置/不可用”
- 仍能正常继续执行其他不依赖该服务的工具

### 4.4 超大输出/长文本（P1）

用例：
- 请求较大范围的市场扫描/报告生成

验收：
- 返回被合理截断或分段
- 不导致客户端渲染卡死

### 4.5 交易类工具（高风险，需你自行确认是否启用）（P0/P1）

用例：
- 在 `paper/testnet` 模式下执行下单/撤单类工具

验收：
- 风控限制生效（白名单、限额、熔断）
- 不会在未明确允许情况下触发真实主网交易

## 5. 问题留痕

一旦出现任何一条失败：

- 先复现一次
- 把失败现象记录到 `lesson/`（复盘）
- 同步更新 `历史记录.json` 与 `任务进度.json`

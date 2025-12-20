# Heablcoin MCP 交易系统

[English](README.md) | [中文](README.zh-CN.md)

> 一个符合 MCP（Model Context Protocol）的智能交易分析/执行助手：模块化、可扩展，并以安全默认值为第一原则。

![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)

## 功能亮点

- 市场分析：技术面/信号/结构/质量等模块化分析，可按需组合。
- 可视化输出：支持结构化 JSON 输出，便于客户端渲染图表。
- 交易与账户：白名单、限额、仓位建议、熔断/预算等安全层。
- 通知与报告：支持邮件报告；云端 Pipeline 支持 Server酱/飞书等可选通道。
- 云端任务：任务发布、状态查询、增强队列（优先级/依赖/超时）、Webhook 回调。
- 量化研究：研究提示词生成与聚合，可选写入 Notion。
- 治理与审计：策略登记、AI 置信度、偏差样本、审计日志（可追溯）。
- 可扩展：多交易所适配、多模型路由、存储适配器（File/Redis/Email/Notion）。

## 架构速览

- 稳定入口：`Heablcoin.py`（MCP stdio）
- 核心运行时：`src/core/server.py`（FastMCP 注册与启动）
- 工具层：`src/tools/*`（对外 MCP Tools）
- 能力层：`src/skills/*`（市场分析/个人绩效/学习/研究/风控/策略/治理/报告）
- 云端模块：`src/core/cloud/*`（任务队列、发布器、API 管理器、worker）
- 存储适配：`src/storage/*`（File/Redis/Email/Notion）
- 通用组件：`src/utils/*`（env、日志、缓存、风控、回测等）

## 快速链接

- [快速开始](docs/user/快速开始.md)
- [安装指南](docs/user/安装指南.md)
- [配置指南](docs/user/配置指南.md)
- [环境变量与 .env 配置说明](env配置说明.md)
- [MCP 配置（Claude/Windsurf/Codex）](docs/user/MCP配置指南.md)
- [MCP 使用指南](docs/user/MCP使用指南.md)
- [API 参考（工具清单）](docs/developer/API参考.md)
- [API 规范（工具与负载）](API_SPEC.md)
- [部署与运维](DEPLOY_GUIDE.md)
- [架构设计](docs/developer/架构设计.md)
- [示例](examples.md)
- [系统化测试指南](docs/developer/系统化测试指南.md)
- [Claude/Windsurf 验收清单](docs/user/验收清单.md)

## 文档索引

### 用户文档
- [文档主页](docs/README.md) - 完整用户与开发者文档入口
- [用户文档入口](docs/user/README.md) - 用户向文档
- [开发者文档入口](docs/developer/README.md) - 开发者向文档
- [代码使用全景图](docs/user/代码使用全景图_按时间轴.md) - 项目演进与使用模式
- [故障排查](docs/user/故障排查.md) - 常见问题与解决方案
- [功能概览](docs/user/功能概览.md) - 系统功能概览

### 开发者文档
- [项目概览](docs/developer/项目概览.md) - 项目高层描述
- [项目记录规范](docs/developer/项目记录规范.md) - 文档与记录规范
- [多端连接集成指南](docs/developer/多端连接集成流程标准化.md) - 集成工作流
- [系统架构图](可视化系统架构.mmd) - 可视化系统架构
- [系统级注入 Prompt](docs/developer/系统级注入%20Prompt.md) - 系统级 Prompt 框架
- [审计专家系统 Prompt](docs/developer/审计专家系统Prompt.md) - 审计框架

## 安装与自检

```bash
pip install -r requirements.txt
cp .env.example .env
python tests/run_tests.py unit
```

## MCP 使用

### Claude Desktop

在 `claude_desktop_config.json` 中添加（示例）：

```json
{
  "mcpServers": {
    "heablcoin": {
      "command": "python",
      "args": ["/absolute/path/to/your/Heablcoin.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

### Windsurf（Codeium MCP）

```json
{
  "mcpServers": {
    "heablcoin": {
      "command": "python",
      "args": ["/absolute/path/to/your/Heablcoin.py"],
      "disabled": false,
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

### Codex CLI

```powershell
codex mcp add heablcoin --env PYTHONIOENCODING=utf-8 --env PYTHONUTF8=1 -- python /absolute/path/to/your/Heablcoin.py
codex mcp list
```

## 开发与测试

```bash
python scripts/check_naming.py
python tests/run_tests.py unit
python tests/run_tests.py integration
python scripts/scan_secrets.py --staged
```

## 安全提示

- 交易相关功能建议优先使用测试网：`.env` 设置 `USE_TESTNET=True`。
- MCP/JSON-RPC 通过 stdio 通信，禁止 `print()` 污染 stdout（日志应写入文件或 stderr）。

## License

本项目使用 [MIT License](LICENSE)。

---

免责声明：本项目仅用于学习与研究。加密货币交易风险极高，请自行评估并承担风险。

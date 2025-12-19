MCP stdout 重定向导致 stdio 启动卡死，发生时间：2025-12-19 15:14:43，模块位置：src/core/server.py，架构环境：MCP Server / Integration Tests
---
### 问题描述
integration 测试（test_mcp_stdio_startup）出现卡死/无响应：客户端等待 stdout 的 JSON-RPC 消息，但实际 stdout 被重定向或被打印污染，导致握手失败。

### 根本原因分析
为避免 stdout 污染，曾直接执行 sys.stdout = sys.stderr，导致 MCP/JSON-RPC 协议通道被改写：协议输出不再写入 stdout，MCP client 无法读取到预期数据，从而卡死。

### 解决方案与步骤
1) 保留 sys.stdout 不变，避免破坏 MCP stdio 协议
2) 通过 monkeypatch builtins.print：未显式指定 file 的 print() 默认写入 stderr
3) 提供开关 MCP_FORCE_PRINT_TO_STDERR（默认 True）与 MCP_REDIRECT_STDOUT（默认 False，仅排障）
4) 补齐/修复 integration 测试入口，确保 CI 可复现

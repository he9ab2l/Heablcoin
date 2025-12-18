# 开发者文档

## 核心文档
1. 项目概览：项目概览.md
2. 架构设计：架构设计.md
3. API参考：API参考.md
4. 路线图：路线图.md

## 模块指南
5. 云端模块指南：云端模块指南.md
6. 个人绩效模块指南：个人绩效模块指南.md
7. 报告系统指南：报告系统指南.md
8. 资源与环境变量：资源与环境变量.md

## Prompt 规范
9. Prompt备忘录：Prompt备忘录.md
10. 审计专家系统 v4.0：审计专家系统_v4.0_Prompt.md
11. 审计与传承专家系统 v5.0：审计与传承专家系统_v5.0_Prompt.md
12. MCP 系统开发提示词：MCP_SYSTEM_DEVELOPMENT_PROMPT_v1.0.md

## 项目记录
13. 项目上下文文档：项目上下文文档.md
14. 运维流程（Runbooks）：runbooks/多端连接集成流程标准化.md

## 版本控制与安全

- Windows（PowerShell）：`.\gp.ps1 "feat: xxx"`
- Linux/macOS（bash）：`./gp.sh "feat: xxx"`
- 提交前自动执行敏感信息扫描：`python scripts/scan_secrets.py --staged`（只输出文件名与命中统计，不输出内容）

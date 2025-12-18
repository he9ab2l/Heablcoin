"""技能层：领域能力（Skills）。

约定：
- `skills.*` 只承载领域能力与可复用业务逻辑，不直接暴露 MCP 接口。
- 对外暴露 MCP 的接口统一放在 `tools.*`（薄封装、可开关、可测试）。
"""

__all__ = ["data", "learning", "market_analysis", "personal_analytics", "report"]


"""MCP tools for AI governance (confidence, bias, audit)."""

from __future__ import annotations

import json
from typing import Any

from core.mcp_safety import mcp_tool_safe
from skills.governance import DecisionConfidenceMonitor, BiasMonitor, AuditTrail


def register_tools(mcp: Any) -> None:
    confidence_monitor = DecisionConfidenceMonitor()
    bias_monitor = BiasMonitor()
    audit_trail = AuditTrail()

    @mcp.tool()
    @mcp_tool_safe
    def score_ai_decision(decision_id: str, inputs_json: str, rationale: str = "", tags: str = "") -> str:
        """为 AI 决策评估置信度并返回执行建议。"""
        inputs = json.loads(inputs_json or "{}")
        payload = confidence_monitor.score(
            decision_id=decision_id,
            inputs=inputs,
            rationale=rationale,
            tags=[t.strip() for t in tags.split(",") if t.strip()],
        )
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def recent_confidence_entries(limit: int = 20) -> str:
        """查看最近的置信度记录。"""
        payload = confidence_monitor.recent(limit=limit)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def record_bias_sample(direction: str, result: str, pnl: float, market_state: str) -> str:
        """记录一次 AI 行为样本用于偏差检测。"""
        payload = bias_monitor.record(direction=direction, result=result, pnl=pnl, market_state=market_state)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def bias_report() -> str:
        """输出偏差检测报告。"""
        payload = bias_monitor.diagnose()
        # Counter type is not JSON serializable, convert to dict
        payload["direction_distribution"] = dict(payload.get("direction_distribution", {}))
        payload["market_state_distribution"] = dict(payload.get("market_state_distribution", {}))
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def log_audit_event(event_type: str, severity: str, payload_json: str = "", requires_ack: bool = False) -> str:
        """写入审计事件流。"""
        payload = json.loads(payload_json or "{}")
        result = audit_trail.log(event_type=event_type, severity=severity, payload=payload, requires_ack=requires_ack)
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool()
    @mcp_tool_safe
    def list_audit_events(limit: int = 50) -> str:
        """列出最近的审计事件。"""
        payload = audit_trail.list_events(limit=limit)
        return json.dumps(payload, ensure_ascii=False, indent=2)


__all__ = ["register_tools"]

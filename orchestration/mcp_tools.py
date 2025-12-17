from __future__ import annotations

import json
from typing import Any

from orchestration.router import build_orchestrator_from_env
from orchestration.tasks import build_plan_for_task, parse_context
from utils.smart_logger import get_logger

logger = get_logger("system")


def register_tools(mcp: Any) -> None:
    orchestrator = build_orchestrator_from_env()

    @mcp.tool()
    def ai_run_pipeline(task: str = "analysis", user_input: str = "", context: str = "") -> str:
        """多阶段多AI流水线：按任务拆分分析/复核/合成"""
        ctx = parse_context(context)
        plan = build_plan_for_task(task=task)
        result = orchestrator.run(plan=plan, user_input=user_input, context=ctx)
        return json.dumps(result, ensure_ascii=False, indent=2)

    @mcp.tool()
    def ai_enhance_output(content: str, tone: str = "concise", context: str = "") -> str:
        """调用多AI链路对输出做二次润色，保持事实一致"""
        ctx = parse_context(context)
        enhanced = orchestrator.enhance_output(content, context=ctx, tone=tone)
        return enhanced.get("final") or json.dumps(enhanced, ensure_ascii=False, indent=2)

    @mcp.tool()
    def ai_provider_snapshot() -> str:
        """查看当前可用AI提供商与路由"""
        providers = []
        for name, provider in orchestrator.providers.items():
            providers.append({"name": name, "model": getattr(provider, "model", ""), "type": provider.__class__.__name__})
        routes = getattr(orchestrator, "role_routes", {})
        info = {
            "providers": providers,
            "routes": routes,
            "default": orchestrator.default_provider,
        }
        return json.dumps(info, ensure_ascii=False, indent=2)

from __future__ import annotations
import json
from typing import Any
from core.mcp_safety import mcp_tool_safe
from core.orchestration.router import build_orchestrator_from_env
from core.orchestration.tasks import build_plan_for_task, parse_context
from core.orchestration.ai_roles import (


    call_ai, AIRole, AIResponse,
    reason, write, remember, research, critique,
    ROLE_CONFIGS
)
from utils.smart_logger import get_logger
from core.orchestration.providers import build_default_providers
from core.cloud.task_manager import enqueue_monitor_task
from storage.notion_adapter import NotionAdapter
from storage.redis_adapter import RedisAdapter


logger = get_logger("system")


def register_tools(mcp: Any) -> None:
    orchestrator = build_orchestrator_from_env()
    @mcp.tool()
    @mcp_tool_safe
    def ai_run_pipeline(task: str = "analysis", user_input: str = "", context: str = "") -> str:
        """多阶段多AI流水线：按任务拆分分析/复核/合成"""
        ctx = parse_context(context)
        plan = build_plan_for_task(task=task)
        result = orchestrator.run(plan=plan, user_input=user_input, context=ctx)
        return json.dumps(result, ensure_ascii=False, indent=2)
    @mcp.tool()
    @mcp_tool_safe
    def ai_enhance_output(content: str, tone: str = "concise", context: str = "") -> str:
        """调用多AI链路对输出做二次润色，保持事实一致"""
        ctx = parse_context(context)
        enhanced = orchestrator.enhance_output(content, context=ctx, tone=tone)
        return enhanced.get("final") or json.dumps(enhanced, ensure_ascii=False, indent=2)
    @mcp.tool()
    @mcp_tool_safe
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
    # ============================================
    # 新增：AI 角色调用工具
    # ============================================
    @mcp.tool()
    @mcp_tool_safe
    def ai_call_role(
        role: str,
        prompt: str,
        context: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        forced_endpoint: str = ""
    ) -> str:
        """
        根据角色调用 AI（统一接口）
        Args:
            role: 角色标识 (ai_reasoning, ai_writer, ai_memory, ai_research, ai_critic)
            prompt: 提示词
            context: 可选的上下文 JSON
            max_tokens: 最大生成长度
            temperature: 随机性 (0-1)
            forced_endpoint: 指定端点名称（可选）
        Returns:
            AI 响应结果
        """
        ctx = json.loads(context) if context else None
        response = call_ai(
            role=role,
            prompt=prompt,
            context=ctx,
            max_tokens=max_tokens,
            temperature=temperature,
            forced_endpoint=forced_endpoint if forced_endpoint else None
        )
        return json.dumps({
            "success": response.success,
            "content": response.content,
            "endpoint": response.endpoint,
            "role": response.role,
            "latency": response.latency,
            "parsed": response.parsed,
            "error": response.error
        }, ensure_ascii=False, indent=2)
    @mcp.tool()
    @mcp_tool_safe
    def ai_reason(prompt: str, context: str = "") -> str:
        """
        AI 推理分析（风险评估、策略审核）
        Args:
            prompt: 分析问题或内容
            context: 可选的上下文 JSON
        """
        ctx = json.loads(context) if context else None
        response = reason(prompt, context=ctx)
        return json.dumps({
            "success": response.success,
            "content": response.content,
            "parsed": response.parsed,
            "error": response.error
        }, ensure_ascii=False, indent=2)
    @mcp.tool()
    @mcp_tool_safe
    def ai_write(prompt: str, tone: str = "professional") -> str:
        """
        AI 写作（报告、日记、邮件）
        Args:
            prompt: 写作要求
            tone: 语气 (professional, casual, formal)
        """
        response = write(prompt, context={"tone": tone})
        return response.content if response.success else f"错误: {response.error}"
    @mcp.tool()
    @mcp_tool_safe
    def ai_remember(prompt: str, documents: str = "") -> str:
        """
        AI 记忆/摘要（长文本分析、历史回顾）
        Args:
            prompt: 分析问题
            documents: 文档内容（用换行分隔多个文档）
        """
        docs = documents.split("\n---\n") if documents else None
        response = remember(prompt, documents=docs)
        return json.dumps({
            "success": response.success,
            "content": response.content,
            "parsed": response.parsed,
            "error": response.error
        }, ensure_ascii=False, indent=2)
    @mcp.tool()
    @mcp_tool_safe
    def ai_research(query: str, num_sources: int = 5) -> str:
        """
        AI 研究（新闻搜索、公告分析）
        Args:
            query: 搜索关键词
            num_sources: 来源数量
        """
        response = research(query, num_sources=num_sources)
        return json.dumps({
            "success": response.success,
            "content": response.content,
            "parsed": response.parsed,
            "error": response.error
        }, ensure_ascii=False, indent=2)
    @mcp.tool()
    @mcp_tool_safe
    def ai_critique(plan: str, criteria: str = "") -> str:
        """
        AI 审查/批评（策略审核、风险识别）
        Args:
            plan: 待审查的计划或策略
            criteria: 审查标准（逗号分隔）
        """
        criteria_list = [c.strip() for c in criteria.split(",") if c.strip()] if criteria else None
        response = critique(plan, criteria=criteria_list)
        return json.dumps({
            "success": response.success,
            "content": response.content,
            "parsed": response.parsed,
            "error": response.error
        }, ensure_ascii=False, indent=2)
    @mcp.tool()
    @mcp_tool_safe
    def ai_list_roles() -> str:
        """列出所有可用的 AI 角色及其说明"""
        roles = []
        for role, config in ROLE_CONFIGS.items():
            roles.append({
                "role": role.value,
                "description": config.description,
                "preferred_endpoints": config.preferred_endpoints,
                "output_format": config.output_format,
                "default_temperature": config.default_temperature
            })
        return json.dumps(roles, ensure_ascii=False, indent=2)
    # ==========================================================
    # 云端协同增强
    # ==========================================================
    @mcp.tool()
    @mcp_tool_safe
    def consult_external_expert(query: str, model: str = "deepseek", context: str = "") -> str:
        """
        让 Claude 借助其他 AI（多云）给出第二意见。
        Args:
            query: 提示/问题
            model: provider 名称（openai/deepseek/anthropic/gemini/groq/moonshot/zhipu）
            context: 可选 JSON 字符串
        """
        providers = build_default_providers()
        provider = providers.get(model)
        if not provider:
            return json.dumps({"success": False, "error": f"model {model} not available"}, ensure_ascii=False, indent=2)
        ctx = json.loads(context) if context else {}
        prompt = query
        if ctx:
            prompt += f"\n\nContext:\n{json.dumps(ctx, ensure_ascii=False, indent=2)}"
        resp = provider.generate(prompt=prompt, system=ctx.get("system_prompt", ""), max_tokens=512, temperature=0.3)
        return json.dumps({
            "success": True,
            "provider": resp.provider or model,
            "model": resp.model,
            "latency": resp.latency,
            "content": resp.text,
        }, ensure_ascii=False, indent=2)
    @mcp.tool()
    @mcp_tool_safe
    def set_cloud_sentry(symbol: str, condition: str, action: str = "notify", notes: str = "") -> str:
        """
        写入云端哨兵任务（Redis 队列），由青龙 worker 轮询执行。
        condition 支持 price < X / price <= X / price > X / price >= X。
        """
        task = {
            "symbol": symbol,
            "condition": condition,
            "action": action,
            "notes": notes,
        }
        result = enqueue_monitor_task(task)
        return json.dumps(result, ensure_ascii=False, indent=2)
    @mcp.tool()
    @mcp_tool_safe
    def sync_session_to_notion(summary: str, tags: str = "") -> str:
        """
        将当前会话/分析结论写入 Notion 日志库。
        需要 NOTION_API_KEY / NOTION_DATABASE_ID（或 REPORTS_DB_ID）。
        """
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]
        adapter = NotionAdapter()
        res = adapter.append_daily_log(summary, tags=tags_list)
        return json.dumps({
            "success": res.success,
            "location": res.location,
            "message": res.message,
            "error": res.error,
        }, ensure_ascii=False, indent=2)
    @mcp.tool()
    @mcp_tool_safe
    def fetch_portfolio_snapshot() -> str:
        """
        返回账户资产快照（调用 Heablcoin.get_account_summary）。
        """
        try:
            from Heablcoin import get_account_summary  # type: ignore


            data = get_account_summary()
            return json.dumps({"success": True, "data": data}, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False, indent=2)
    @mcp.tool()
    @mcp_tool_safe
    def get_learning_context() -> str:
        """
        返回最近的交易教训/偏好，来自 dev/lessons.md（如不存在则返回占位提示）。
        """
        import os
        from utils.project_paths import PROJECT_ROOT


        path = str(PROJECT_ROOT / "dev" / "lessons.md")
        if not os.path.exists(path):
            return "暂无 lessons，可在 dev/lessons.md 中添加你的教训/偏好。"
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return content.strip() or "文件为空，请填入教训/偏好。"
        except Exception as e:
            return f"读取失败: {e}"

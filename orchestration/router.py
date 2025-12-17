from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from orchestration.providers import AiProvider, ProviderResponse, EchoProvider, build_default_providers
from utils.smart_logger import get_logger

logger = get_logger("system")


class _SafeDict(dict):
    """Dict with graceful fallback for missing keys in format strings."""

    def __missing__(self, key: str) -> str:
        return ""


@dataclass
class AiTaskStep:
    name: str
    role: str
    prompt_template: str
    provider: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 512

    def render_prompt(self, user_input: str, context: Dict[str, Any], previous_outputs: Dict[str, str]) -> str:
        payload = _SafeDict(
            {
                "user_input": user_input or "",
                "context_json": json.dumps(context or {}, ensure_ascii=False, indent=2),
                "previous": previous_outputs,
            }
        )
        payload.update({f"prev_{k}": v for k, v in previous_outputs.items()})
        try:
            return self.prompt_template.format_map(payload)
        except Exception:
            return f"{self.prompt_template}\n\nUser input:\n{user_input}\n\nContext:\n{payload.get('context_json', '')}"


@dataclass
class AiTaskPlan:
    name: str
    description: str
    steps: List[AiTaskStep] = field(default_factory=list)


class MultiAIOrchestrator:
    """Routes sub-tasks to different AI providers."""

    def __init__(
        self,
        providers: Optional[Dict[str, AiProvider]] = None,
        role_routes: Optional[Dict[str, str]] = None,
        default_provider: Optional[str] = None,
    ) -> None:
        self.providers = providers or build_default_providers()
        self.role_routes = role_routes or {}
        self.default_provider = default_provider or next(iter(self.providers.keys()))

    def _choose_provider(self, role: str, preferred: Optional[str] = None) -> AiProvider:
        if preferred and preferred in self.providers:
            return self.providers[preferred]
        route = self.role_routes.get(role)
        if route and route in self.providers:
            return self.providers[route]
        if self.default_provider in self.providers:
            return self.providers[self.default_provider]
        return next(iter(self.providers.values()), EchoProvider())

    def run(self, plan: AiTaskPlan, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = context or {}
        outputs: Dict[str, str] = {}
        steps_result: Dict[str, Any] = {}

        for step in plan.steps:
            provider = self._choose_provider(step.role, step.provider)
            prompt = step.render_prompt(user_input=user_input, context=ctx, previous_outputs=outputs)
            logger.info(f"[AI Router] step={step.name} provider={provider.name}")
            response: ProviderResponse = provider.generate(
                prompt=prompt, system=ctx.get("system_prompt", ""), max_tokens=step.max_tokens, temperature=step.temperature
            )
            outputs[step.name] = response.text
            steps_result[step.name] = {
                "provider": response.provider or provider.name,
                "model": response.model or getattr(provider, "model", ""),
                "latency": response.latency,
                "output": response.text,
            }

        final_key = plan.steps[-1].name if plan.steps else ""
        return {
            "task": plan.name,
            "description": plan.description,
            "steps": steps_result,
            "final": outputs.get(final_key, ""),
        }

    def enhance_output(self, content: str, context: Optional[Dict[str, Any]] = None, tone: str = "concise") -> Dict[str, Any]:
        plan = build_output_enhance_plan(tone=tone)
        ctx = context or {}
        ctx.setdefault("system_prompt", "You improve trading assistant outputs while preserving facts.")
        return self.run(plan=plan, user_input=content, context=ctx)


def build_output_enhance_plan(tone: str = "concise") -> AiTaskPlan:
    steps = [
        AiTaskStep(
            name="draft",
            role="analysis",
            provider=None,
            temperature=0.4,
            max_tokens=400,
            prompt_template=(
                "Rewrite the following trading assistant output to improve clarity and readability for end users.\n"
                "Keep structure similar but make it easier to scan. Tone: {tone}. Use bullet points where helpful.\n"
                "Content:\n{user_input}\n\nContext:\n{context_json}"
            ).format(tone=tone),
        ),
        AiTaskStep(
            name="review",
            role="safety",
            provider=None,
            temperature=0.2,
            max_tokens=240,
            prompt_template=(
                "You are a reviewer. Check the draft for hallucinations or missing risk callouts.\n"
                "Draft:\n{prev_draft}\n\nContext:\n{context_json}\n\n"
                "Return the corrected draft only."
            ),
        ),
        AiTaskStep(
            name="finalize",
            role="synthesis",
            provider=None,
            temperature=0.2,
            max_tokens=320,
            prompt_template="Tighten the reviewed draft into the final answer. Keep it short.\n\nDraft:\n{prev_review}",
        ),
    ]
    return AiTaskPlan(name="output_enhance", description="Rewrite and validate user-facing output", steps=steps)


def build_default_task_plan(task: str = "analysis") -> AiTaskPlan:
    task_key = (task or "").lower().strip()
    if task_key == "risk":
        steps = [
            AiTaskStep(
                name="risk_scan",
                role="analysis",
                provider=None,
                temperature=0.2,
                max_tokens=400,
                prompt_template=(
                    "Scan the scenario for risk flags and operational hazards. Keep the answer concise.\n\n"
                    "Scenario:\n{user_input}\n\nContext:\n{context_json}"
                ),
            ),
            AiTaskStep(
                name="advisor",
                role="safety",
                provider=None,
                temperature=0.3,
                max_tokens=320,
                prompt_template="Turn the risk scan into 3-5 concrete safeguards for the user.\n\nNotes:\n{prev_risk_scan}",
            ),
        ]
        return AiTaskPlan(name="risk_review", description="Two-stage risk scan + guidance", steps=steps)

    steps = [
        AiTaskStep(
            name="analysis",
            role="analysis",
            provider=None,
            temperature=0.4,
            max_tokens=640,
            prompt_template=(
                "You are a trading analyst. Break down the task step-by-step and surface the key takeaways.\n"
                "Task:\n{user_input}\n\nContext:\n{context_json}"
            ),
        ),
        AiTaskStep(
            name="critique",
            role="critique",
            provider=None,
            temperature=0.2,
            max_tokens=360,
            prompt_template="Critique the analysis above. Fix gaps or math errors. Keep concise.\n\nDraft:\n{prev_analysis}",
        ),
        AiTaskStep(
            name="final",
            role="synthesis",
            provider=None,
            temperature=0.3,
            max_tokens=420,
            prompt_template="Summarize the critique-adjusted draft into a user-facing answer.\n\nInput:\n{prev_critique}",
        ),
    ]
    return AiTaskPlan(name="multi_ai_default", description="Analysis -> critique -> final synthesis", steps=steps)


def build_orchestrator_from_env() -> MultiAIOrchestrator:
    providers = build_default_providers()
    role_routes: Dict[str, str] = {}
    if os.getenv("AI_ROUTE_ANALYSIS"):
        role_routes["analysis"] = os.getenv("AI_ROUTE_ANALYSIS", "")
    if os.getenv("AI_ROUTE_CRITIQUE"):
        role_routes["critique"] = os.getenv("AI_ROUTE_CRITIQUE", "")
    if os.getenv("AI_ROUTE_SYNTHESIS"):
        role_routes["synthesis"] = os.getenv("AI_ROUTE_SYNTHESIS", "")
    if os.getenv("AI_ROUTE_SAFETY"):
        role_routes["safety"] = os.getenv("AI_ROUTE_SAFETY", "")
    default_provider = os.getenv("AI_DEFAULT_PROVIDER")
    return MultiAIOrchestrator(providers=providers, role_routes=role_routes, default_provider=default_provider)

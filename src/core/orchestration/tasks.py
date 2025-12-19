############################################################
# 📘 文件说明：
# 本文件实现的功能：风控相关模块：提供风险控制、资金管理与限制规则。
#
# 📋 程序整体伪代码（中文）：
# 1. 初始化主要依赖与变量
# 2. 加载输入数据或接收外部请求
# 3. 执行主要逻辑步骤（如计算、处理、训练、渲染等）
# 4. 输出或返回结果
# 5. 异常处理与资源释放
#
# 🔄 程序流程图（逻辑流）：
# ┌──────────┐
# │  输入数据 │
# └─────┬────┘
#       ↓
# ┌────────────┐
# │  核心处理逻辑 │
# └─────┬──────┘
#       ↓
# ┌──────────┐
# │  输出结果 │
# └──────────┘
#
# 📊 数据管道说明：
# 数据流向：输入源 → 数据清洗/转换 → 核心算法模块 → 输出目标（文件 / 接口 / 终端）
#
# 🧩 文件结构：
# - 依赖（标准库）：__future__, json, typing
# - 依赖（第三方）：无
# - 依赖（本地）：.router
#
# 🕒 创建时间：2025-12-19
############################################################

from __future__ import annotations

import json
from typing import Any, Dict

from .router import AiTaskPlan, AiTaskStep


def build_plan_for_task(task: str, tone: str = "concise") -> AiTaskPlan:
    key = (task or "").lower().strip()
    if key in {"output", "rewrite", "enhance"}:
        return AiTaskPlan(
            name="output_enhance",
            description="Rewrite user-facing output for readability",
            steps=[
                AiTaskStep(
                    name="rewrite",
                    role="analysis",
                    temperature=0.4,
                    max_tokens=480,
                    prompt_template=(
                        "Rewrite the following response for clarity. Keep factual content. Tone: {tone}.\n\n"
                        "Original:\n{user_input}\n\nContext:\n{context_json}"
                    ).format(tone=tone),
                ),
                AiTaskStep(
                    name="review",
                    role="safety",
                    temperature=0.2,
                    max_tokens=280,
                    prompt_template="Check the rewrite for hallucinations or missing risk notes. Provide corrected text only.\n\nDraft:\n{prev_rewrite}",
                ),
            ],
        )
    if key in {"risk", "guardrail"}:
        return AiTaskPlan(
            name="risk_guard",
            description="Risk scan + guardrail recommendations",
            steps=[
                AiTaskStep(
                    name="scan",
                    role="analysis",
                    temperature=0.2,
                    max_tokens=420,
                    prompt_template="Identify the top 5 risks in the scenario below. Keep concise.\n\nScenario:\n{user_input}\n\nContext:\n{context_json}",
                ),
                AiTaskStep(
                    name="actions",
                    role="synthesis",
                    temperature=0.25,
                    max_tokens=320,
                    prompt_template="Turn the risks into concrete mitigation steps for the user.\n\nRisks:\n{prev_scan}",
                ),
            ],
        )

    return AiTaskPlan(
        name="multi_ai_default",
        description="General multi-AI pipeline",
        steps=[
            AiTaskStep(
                name="analysis",
                role="analysis",
                temperature=0.4,
                max_tokens=620,
                prompt_template="Break down the user task step-by-step. Keep it short and actionable.\n\nTask:\n{user_input}\n\nContext:\n{context_json}",
            ),
            AiTaskStep(
                name="safety",
                role="safety",
                temperature=0.25,
                max_tokens=300,
                prompt_template="Check the analysis for unsafe steps or data gaps. Fix if needed and return the improved version.\n\nDraft:\n{prev_analysis}",
            ),
        ],
    )


def parse_context(context: str) -> Dict[str, Any]:
    if not context:
        return {}
    try:
        return json.loads(context)
    except Exception:
        return {"context": context}

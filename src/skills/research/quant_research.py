############################################################
# 📘 文件说明：
# 本文件实现的功能：Quantitative research helper utilities.
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
# - 依赖（标准库）：__future__, dataclasses, datetime, json, typing
# - 依赖（第三方）：无
# - 依赖（本地）：core.orchestration.ai_roles, storage.notion_adapter, utils.smart_logger
#
# 🕒 创建时间：2025-12-19
############################################################

"""Quantitative research helper utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from core.orchestration.ai_roles import (
    AIRole,
    AIResponse,
    call_ai,
    research as ai_research_call,
)
from storage.notion_adapter import NotionAdapter
from utils.smart_logger import get_logger

logger = get_logger("quant_research")


FOCUS_HINTS: Dict[str, str] = {
    "balanced": "同时评估 alpha 机会、风险事件、资金流与执行条件，输出全面视角",
    "alpha": "聚焦可操作的 alpha 来源（错价、结构性机会、事件驱动、统计套利）",
    "risk": "强调尾部风险、杠杆脆弱性、资金链断裂、政策不确定性",
    "macro": "纳入宏观与跨市场信息，观察美元流动性、收益率曲线、央行指引",
}


@dataclass(frozen=True)
class ResearchSection:
    """Prompt template metadata."""

    identifier: str
    title: str
    prompt_template: str


SECTION_PRESETS: List[ResearchSection] = [
    ResearchSection(
        identifier="market_regime",
        title="市场结构与波动率",
        prompt_template=(
            "围绕 {topic} ，总结当前市场结构、波动率状态以及微观结构信号。"
            "请量化描述（如 realized/ implied vol、订单簿深度、持仓集中度），并着重 {lens} 。"
            "输出要点 + 数据来源。"
        ),
    ),
    ResearchSection(
        identifier="flow_and_depth",
        title="资金流向与深度",
        prompt_template=(
            "调研 {topic} 相关的资金流向（链上、交易所、基金）与流动性深度。"
            "标注鲸鱼/机构/ETF 等关键主体动向，结合 {lens} 说明潜在影响。"
        ),
    ),
    ResearchSection(
        identifier="derivatives",
        title="衍生品与杠杆",
        prompt_template=(
            "针对 {topic} ，梳理永续、期权等衍生品指标（资金费率、IV 曲面、OI 分布）。"
            "说明杠杆结构对 {lens} 的提示。"
        ),
    ),
    ResearchSection(
        identifier="alpha_streams",
        title="可执行 Alpha 线索",
        prompt_template=(
            "列举与 {topic} 相关的 2-3 条潜在 alpha 或交易思路（跨期、跨品、统计关系、链上数据）。"
            "要求结合 {lens} ，给出假设、触发条件、数据来源。"
        ),
    ),
    ResearchSection(
        identifier="risk_radar",
        title="风险事件与防御",
        prompt_template=(
            "盘点与 {topic} 有关的主要风险事件（政策、技术、清算、资方行为），"
            "并结合 {lens} 给出监控指标与防御建议。"
        ),
    ),
]


def _normalize_focus(focus: str) -> str:
    key = (focus or "balanced").strip().lower()
    if key not in FOCUS_HINTS:
        key = "balanced"
    return key


def generate_quant_prompts(
    topic: str,
    focus: str = "balanced",
    sections: Optional[Iterable[str]] = None,
) -> List[Dict[str, str]]:
    """Return prompt set for quant research."""
    focus_key = _normalize_focus(focus)
    selected_ids = {s.strip() for s in sections or [] if s.strip()}
    prompts: List[Dict[str, str]] = []
    for section in SECTION_PRESETS:
        if selected_ids and section.identifier not in selected_ids:
            continue
        prompt_text = section.prompt_template.format(topic=topic, lens=FOCUS_HINTS[focus_key])
        prompts.append(
            {
                "id": section.identifier,
                "title": section.title,
                "prompt": prompt_text,
            }
        )
    return prompts


def _summarize_sections(topic: str, focus: str, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    raw_bundle = json.dumps(sections, ensure_ascii=False, indent=2)
    summary_prompt = f"""
你是资深量化研究主管。主题: {topic} 。视角: {focus} 。
请阅读以下 JSON 中的研究摘要，输出 JSON，包含:
- \"market_snapshot\": 核心态势描述（字符串）
- \"alpha_ideas\": 1-3 条可执行想法（数组）
- \"risk_notes\": 主要风险提示（数组）
- \"data_sources\": 重要来源（数组）

<research>
{raw_bundle}
</research>
"""
    response = call_ai(
        role=AIRole.REASONING,
        prompt=summary_prompt,
        max_tokens=1200,
        temperature=0.25,
    )
    parsed: Optional[Dict[str, Any]] = None
    if response.success:
        try:
            parsed = json.loads(response.content)
        except json.JSONDecodeError:
            parsed = None
    return {
        "raw": response.content,
        "parsed": parsed,
        "success": response.success,
        "error": response.error,
        "endpoint": response.endpoint,
    }


def _build_markdown(
    topic: str,
    focus: str,
    prompts: List[Dict[str, str]],
    sections: List[Dict[str, Any]],
    summary: Dict[str, Any],
) -> str:
    lines = [
        f"# {topic} 量化研究快报",
        "",
        f"- 研究视角: **{focus}**",
        f"- 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 结构化摘要",
    ]
    parsed = summary.get("parsed") or {}
    if parsed:
        lines.append("```json")
        lines.append(json.dumps(parsed, ensure_ascii=False, indent=2))
        lines.append("```")
    else:
        lines.append(summary.get("raw") or "暂无摘要")
    lines.append("")
    for section, prompt in zip(sections, prompts):
        lines.append(f"## {prompt['title']}")
        lines.append(f"**Prompt**: {prompt['prompt']}")
        if section.get("success"):
            lines.append("**Result**:")
            lines.append(section.get("content") or "")
        else:
            lines.append(f"**Error**: {section.get('error')}")
        lines.append("")
    return "\n".join(lines).strip()


def execute_quant_research(
    topic: str,
    *,
    focus: str = "balanced",
    sections: Optional[Iterable[str]] = None,
    num_sources: int = 4,
    save_to_notion: bool = False,
    tags: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Run ai_research across curated prompts and aggregate results."""
    prompts = generate_quant_prompts(topic=topic, focus=focus, sections=sections)
    outputs: List[Dict[str, Any]] = []
    for prompt in prompts:
        resp: AIResponse = ai_research_call(prompt["prompt"], num_sources=num_sources)
        entry = {
            "section": prompt["id"],
            "title": prompt["title"],
            "prompt": prompt["prompt"],
            "success": resp.success,
            "content": resp.content,
            "error": resp.error,
            "endpoint": resp.endpoint,
        }
        outputs.append(entry)
    summary = _summarize_sections(topic, focus, outputs)
    markdown = _build_markdown(topic, focus, prompts, outputs, summary)
    notion_payload: Optional[Dict[str, Any]] = None
    if save_to_notion:
        adapter = NotionAdapter()
        storage = adapter.save_report(
            title=f"{topic} Quant Research",
            content=markdown,
            report_type="QuantResearch",
            symbol=topic,
            tags=[t.strip() for t in (tags or []) if t.strip()],
        )
        notion_payload = {
            "success": storage.success,
            "location": storage.location,
            "message": storage.message,
            "error": storage.error,
        }
    return {
        "topic": topic,
        "focus": focus,
        "prompts": prompts,
        "sections": outputs,
        "summary": summary,
        "notion": notion_payload,
        "generated_at": datetime.now().isoformat(),
    }


__all__ = ["generate_quant_prompts", "execute_quant_research"]

"""
AI 角色调用规范
================
根据计划书设计的统一 AI 调用接口，将"调用某个模型"抽象成"调用某个角色"。
每个角色封装了任务类型、优先级以及返回格式，并交由 ApiManager 自行选择最佳端点。

角色列表：
- ai_reasoning: 复杂推理、风险评估、策略审核
- ai_writer: 撰写报告、日记、邮件
- ai_memory: 长上下文摘要、历史回顾
- ai_research: 联网搜索和摘要新闻
- ai_critic: 挑刺和生成反例、审查交易计划
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum

from core.cloud.api_manager import ApiManager, ApiEndpoint, get_api_manager
from utils.smart_logger import get_logger

logger = get_logger("ai_roles")


class AIRole(str, Enum):
    """AI 角色枚举"""
    REASONING = "ai_reasoning"    # 复杂推理、风险评估、策略审核
    WRITER = "ai_writer"          # 撰写报告、日记、邮件
    MEMORY = "ai_memory"          # 长上下文摘要、历史回顾
    RESEARCH = "ai_research"      # 联网搜索和摘要新闻
    CRITIC = "ai_critic"          # 挑刺和生成反例


@dataclass
class RoleConfig:
    """角色配置"""
    role: AIRole
    description: str
    preferred_endpoints: List[str]  # 优先使用的端点名称
    system_prompt: str
    default_max_tokens: int = 1024
    default_temperature: float = 0.7
    output_format: str = "text"  # text, json, markdown


@dataclass
class AIResponse:
    """AI 调用响应"""
    content: str
    endpoint: str
    role: str
    latency: float
    raw: Optional[Dict] = None
    parsed: Optional[Dict] = None
    success: bool = True
    error: Optional[str] = None


# 角色配置定义
ROLE_CONFIGS: Dict[AIRole, RoleConfig] = {
    AIRole.REASONING: RoleConfig(
        role=AIRole.REASONING,
        description="负责复杂推理、风险评估、策略审核。用于判断交易信号是否合理或解读异常现象。",
        preferred_endpoints=["openai", "anthropic", "deepseek"],
        system_prompt="""你是一个专业的量化交易策略分析师，擅长：
- 复杂推理和逻辑分析
- 风险评估和策略审核
- 解读市场异常现象
- 判断交易信号的合理性

请以结构化的方式输出你的分析结果，包含决策建议和详细解释。""",
        default_max_tokens=1024,
        default_temperature=0.3,
        output_format="json"
    ),
    
    AIRole.WRITER: RoleConfig(
        role=AIRole.WRITER,
        description="负责撰写人类可读的报告、日记、邮件等。强调可读性和中文能力。",
        preferred_endpoints=["deepseek", "openai", "anthropic"],
        system_prompt="""你是一个专业的金融报告撰写专家，擅长：
- 撰写清晰、专业的中文报告
- 将复杂数据转化为易读的文字
- 使用恰当的格式（Markdown）
- 保持专业但易于理解的语气

请以 Markdown 格式输出，使用适当的标题、列表和强调。""",
        default_max_tokens=2048,
        default_temperature=0.7,
        output_format="markdown"
    ),
    
    AIRole.MEMORY: RoleConfig(
        role=AIRole.MEMORY,
        description="负责处理长上下文摘要、历史回顾。适用于个人行为分析、长周期行情解释。",
        preferred_endpoints=["gemini", "anthropic", "openai"],
        system_prompt="""你是一个专业的交易行为分析师，擅长：
- 分析长期交易历史和行为模式
- 总结关键趋势和转折点
- 识别交易习惯和偏好
- 提供基于历史的洞察

请提供结构化的摘要和洞察。""",
        default_max_tokens=2048,
        default_temperature=0.5,
        output_format="json"
    ),
    
    AIRole.RESEARCH: RoleConfig(
        role=AIRole.RESEARCH,
        description="负责联网搜索和摘要新闻、公告、链上数据。",
        preferred_endpoints=["tavily", "groq", "openai"],
        system_prompt="""你是一个专业的加密货币研究分析师，擅长：
- 搜索和分析市场新闻
- 解读公告和政策变化
- 分析链上数据和趋势
- 提供信息来源和可信度评估

请提供带有来源链接的结构化信息。""",
        default_max_tokens=1024,
        default_temperature=0.5,
        output_format="json"
    ),
    
    AIRole.CRITIC: RoleConfig(
        role=AIRole.CRITIC,
        description="负责挑刺和生成反例，例如审查交易计划、挑出潜在风险。",
        preferred_endpoints=["anthropic", "openai", "deepseek"],
        system_prompt="""你是一个严格的交易风险审查官，职责是：
- 审查交易计划和策略
- 识别潜在风险和漏洞
- 提出反对意见和反例
- 评估风险等级

请以批判性思维分析，指出所有可能的问题。输出风险等级（低/中/高/极高）和具体建议。""",
        default_max_tokens=1024,
        default_temperature=0.4,
        output_format="json"
    ),
}


def get_role_config(role: Union[str, AIRole]) -> RoleConfig:
    """获取角色配置"""
    if isinstance(role, str):
        role = AIRole(role)
    return ROLE_CONFIGS.get(role)


def call_ai(
    role: Union[str, AIRole],
    prompt: str,
    *,
    context: Optional[Dict] = None,
    schema: Optional[Dict] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    forced_endpoint: Optional[str] = None,
    system_override: Optional[str] = None,
) -> AIResponse:
    """
    根据角色调用适当的 API 端点。返回结构化数据或文本。

    Args:
        role: 角色标识，如 ai_writer/ai_reasoning。
        prompt: 主提示词。
        context: 可选的额外上下文，如历史记录、表格等。
        schema: 可选的 JSON 模式，要求模型输出符合结构。
        max_tokens: 最大生成长度。
        temperature: 随机性。
        forced_endpoint: 指定 API 端点，优先级高于配置。
        system_override: 覆盖默认的系统提示词。

    Returns:
        AIResponse: 包含模型返回内容和所用端点信息。
    """
    start_time = time.time()
    
    # 获取角色配置
    if isinstance(role, str):
        try:
            role_enum = AIRole(role)
        except ValueError:
            return AIResponse(
                content="",
                endpoint="",
                role=role,
                latency=0,
                success=False,
                error=f"Unknown role: {role}"
            )
    else:
        role_enum = role
    
    config = get_role_config(role_enum)
    if not config:
        return AIResponse(
            content="",
            endpoint="",
            role=role_enum.value,
            latency=0,
            success=False,
            error=f"No config found for role: {role_enum.value}"
        )
    
    # 构建完整提示词
    system_prompt = system_override or config.system_prompt
    
    if context:
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        full_prompt = f"{prompt}\n\n### 上下文信息\n```json\n{context_str}\n```"
    else:
        full_prompt = prompt
    
    if schema:
        schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
        full_prompt += f"\n\n### 输出格式要求\n请按以下 JSON 模式输出：\n```json\n{schema_str}\n```"
    
    # 设置参数
    tokens = max_tokens or config.default_max_tokens
    temp = temperature if temperature is not None else config.default_temperature
    
    # 获取 API 管理器
    api_manager = get_api_manager()
    
    # 选择端点策略
    if forced_endpoint:
        # 强制使用指定端点
        endpoint = api_manager.get_endpoint(forced_endpoint)
        if not endpoint:
            return AIResponse(
                content="",
                endpoint=forced_endpoint,
                role=role_enum.value,
                latency=0,
                success=False,
                error=f"Endpoint not found: {forced_endpoint}"
            )
        endpoints_to_try = [endpoint]
    else:
        # 按优先级获取可用端点
        endpoints_to_try = []
        for ep_name in config.preferred_endpoints:
            ep = api_manager.get_endpoint(ep_name)
            if ep and api_manager.is_endpoint_available(ep_name):
                endpoints_to_try.append(ep)
        
        # 如果优先端点都不可用，获取任意可用端点
        if not endpoints_to_try:
            available = api_manager.get_available_endpoints()
            endpoints_to_try = available[:3]  # 最多尝试3个
    
    if not endpoints_to_try:
        return AIResponse(
            content="",
            endpoint="",
            role=role_enum.value,
            latency=time.time() - start_time,
            success=False,
            error="No available API endpoints"
        )
    
    # 尝试调用
    last_error = None
    for endpoint in endpoints_to_try:
        try:
            logger.info(f"[{role_enum.value}] Trying endpoint: {endpoint.name}")
            
            # 调用 API
            from .providers import OpenAICompatibleProvider
            
            provider = OpenAICompatibleProvider(
                name=endpoint.name,
                api_key=endpoint.api_key,
                base_url=endpoint.base_url,
                model=endpoint.model,
                timeout=endpoint.timeout
            )
            
            response = provider.generate(
                prompt=full_prompt,
                system=system_prompt,
                max_tokens=tokens,
                temperature=temp
            )
            
            if response.text and not response.text.startswith("["):
                # 成功
                latency = time.time() - start_time
                
                # 尝试解析 JSON
                parsed = None
                if config.output_format == "json":
                    try:
                        # 尝试从文本中提取 JSON
                        text = response.text
                        if "```json" in text:
                            text = text.split("```json")[1].split("```")[0]
                        elif "```" in text:
                            text = text.split("```")[1].split("```")[0]
                        parsed = json.loads(text.strip())
                    except:
                        pass
                
                # 更新端点统计
                api_manager.record_success(endpoint.name, latency)
                
                return AIResponse(
                    content=response.text,
                    endpoint=endpoint.name,
                    role=role_enum.value,
                    latency=latency,
                    raw=response.raw,
                    parsed=parsed,
                    success=True
                )
            else:
                last_error = response.text
                api_manager.record_failure(endpoint.name)
                
        except Exception as e:
            last_error = str(e)
            logger.warning(f"[{role_enum.value}] Endpoint {endpoint.name} failed: {e}")
            api_manager.record_failure(endpoint.name)
            continue
    
    # 所有端点都失败
    return AIResponse(
        content="",
        endpoint="",
        role=role_enum.value,
        latency=time.time() - start_time,
        success=False,
        error=f"All endpoints failed. Last error: {last_error}"
    )


def call_ai_async(
    role: Union[str, AIRole],
    prompt: str,
    callback: Optional[Callable[[AIResponse], None]] = None,
    **kwargs
) -> str:
    """
    异步调用 AI，返回任务 ID。
    
    Args:
        role: 角色标识
        prompt: 提示词
        callback: 可选的回调函数
        **kwargs: 其他参数传递给 call_ai
    
    Returns:
        str: 任务 ID
    """
    from core.cloud.enhanced_publisher import EnhancedCloudTaskPublisher, TaskPriority
    
    publisher = EnhancedCloudTaskPublisher()
    
    task = publisher.publish(
        name=f"ai_call_{role}",
        payload={
            "role": role if isinstance(role, str) else role.value,
            "prompt": prompt,
            "kwargs": kwargs
        },
        priority=TaskPriority.NORMAL.value,
        timeout=120.0,
        tags=["ai_call", role if isinstance(role, str) else role.value]
    )
    
    return task.task_id


# 便捷函数
def reason(prompt: str, context: Optional[Dict] = None, **kwargs) -> AIResponse:
    """调用推理角色"""
    return call_ai(AIRole.REASONING, prompt, context=context, **kwargs)


def write(prompt: str, context: Optional[Dict] = None, **kwargs) -> AIResponse:
    """调用写作角色"""
    return call_ai(AIRole.WRITER, prompt, context=context, **kwargs)


def remember(prompt: str, documents: Optional[List[str]] = None, **kwargs) -> AIResponse:
    """调用记忆角色"""
    context = {"documents": documents} if documents else None
    return call_ai(AIRole.MEMORY, prompt, context=context, **kwargs)


def research(query: str, num_sources: int = 5, **kwargs) -> AIResponse:
    """调用研究角色"""
    context = {"num_sources": num_sources}
    return call_ai(AIRole.RESEARCH, query, context=context, **kwargs)


def critique(plan: str, criteria: Optional[List[str]] = None, **kwargs) -> AIResponse:
    """调用批评角色"""
    context = {"criteria": criteria} if criteria else None
    return call_ai(AIRole.CRITIC, plan, context=context, **kwargs)


# 导出
__all__ = [
    "AIRole",
    "RoleConfig",
    "AIResponse",
    "ROLE_CONFIGS",
    "get_role_config",
    "call_ai",
    "call_ai_async",
    "reason",
    "write",
    "remember",
    "research",
    "critique",
]

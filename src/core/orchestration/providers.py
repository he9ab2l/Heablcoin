from __future__ import annotations
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional
from utils.smart_logger import get_logger


logger = get_logger("system")


@dataclass


class ProviderResponse:
    text: str
    latency: float
    raw: Optional[Dict[str, Any]] = None
    provider: str = ""
    model: str = ""


class AiProvider:
    name: str
    model: str
    def generate(self, prompt: str, system: str = "", max_tokens: int = 512, temperature: float = 0.3) -> ProviderResponse:
        raise NotImplementedError


class EchoProvider(AiProvider):
    """Offline fallback provider to keep flows working without network/API keys."""
    def __init__(self, name: str = "echo", model: str = "offline-echo") -> None:
        self.name = name
        self.model = model
    def generate(self, prompt: str, system: str = "", max_tokens: int = 512, temperature: float = 0.3) -> ProviderResponse:
        start = time.time()
        text = f"[{self.name}] {prompt.strip()}"
        return ProviderResponse(text=text, latency=time.time() - start, raw={"echo": True}, provider=self.name, model=self.model)


class OpenAICompatibleProvider(AiProvider):
    """Calls OpenAI-compatible chat completions endpoints."""
    def __init__(self, name: str, api_key: str, base_url: str, model: str, timeout: float = 30.0, max_retries: int = 3) -> None:
        self.name = name
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = model.strip()
        self.timeout = float(timeout)
        self.max_retries = max_retries
    def generate(self, prompt: str, system: str = "", max_tokens: int = 512, temperature: float = 0.3) -> ProviderResponse:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system or "You are a concise trading copilot."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = json.dumps(payload).encode("utf-8")
        last_error = None
        for attempt in range(self.max_retries):
            start = time.time()
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read().decode("utf-8")
                    parsed = json.loads(body)
                    text = parsed.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    return ProviderResponse(text=text, latency=time.time() - start, raw=parsed, provider=self.name, model=self.model)
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else str(e)
                last_error = detail
                logger.warning(f"[{self.name}] HTTP error (attempt {attempt + 1}/{self.max_retries}): {detail}")
                if attempt < self.max_retries - 1:
                    time.sleep(1.5 ** attempt)
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[{self.name}] request failed (attempt {attempt + 1}/{self.max_retries}): {type(e).__name__}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1.5 ** attempt)
        logger.error(f"[{self.name}] All {self.max_retries} attempts failed")
        return ProviderResponse(text=f"[{self.name}] error: {last_error}", latency=0, raw=None, provider=self.name, model=self.model)


class AnthropicProvider(AiProvider):
    """Basic Anthropic messages caller."""
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229", base_url: str = "https://api.anthropic.com/v1/messages", timeout: float = 30.0) -> None:
        self.name = "anthropic"
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = model.strip()
        self.timeout = float(timeout)
    def generate(self, prompt: str, system: str = "", max_tokens: int = 512, temperature: float = 0.3) -> ProviderResponse:
        payload = {
            "model": self.model,
            "system": system or "You are a concise trading copilot.",
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        data = json.dumps(payload).encode("utf-8")
        start = time.time()
        try:
            req = urllib.request.Request(self.base_url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
                parsed = json.loads(body)
                content = parsed.get("content", [])
                text = ""
                if isinstance(content, list) and content:
                    first = content[0] or {}
                    if isinstance(first, dict):
                        text = first.get("text", "") or first.get("content", "")
                if not text:
                    text = parsed.get("content", "") or parsed.get("message", "")
                return ProviderResponse(text=text.strip(), latency=time.time() - start, raw=parsed, provider=self.name, model=self.model)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else str(e)
            logger.error(f"[{self.name}] HTTP error: {detail}")
            return ProviderResponse(text=f"[{self.name}] error: {detail}", latency=time.time() - start, raw=None, provider=self.name, model=self.model)
        except Exception as e:
            logger.error(f"[{self.name}] request failed: {type(e).__name__}: {e}")
            return ProviderResponse(text=f"[{self.name}] error: {e}", latency=time.time() - start, raw=None, provider=self.name, model=self.model)


def build_default_providers() -> Dict[str, AiProvider]:
    """Load providers from environment; always return at least one offline provider."""
    providers: Dict[str, AiProvider] = {}
    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("HEABL_OPENAI_KEY")
    if openai_key:
        providers["openai"] = OpenAICompatibleProvider(
            name="openai",
            api_key=openai_key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            timeout=float(os.getenv("AI_TIMEOUT", "30")),
        )
    deepseek_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("HEABL_DEEPSEEK_KEY")
    if deepseek_key:
        providers["deepseek"] = OpenAICompatibleProvider(
            name="deepseek",
            api_key=deepseek_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            timeout=float(os.getenv("AI_TIMEOUT", "30")),
        )
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        providers["anthropic"] = AnthropicProvider(
            api_key=anthropic_key,
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229"),
            base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1/messages"),
            timeout=float(os.getenv("AI_TIMEOUT", "30")),
        )
    if not providers:
        providers["echo"] = EchoProvider()
    else:
        providers["echo"] = EchoProvider()
    groq_key = os.getenv("GROQ_API_KEY") or os.getenv("HEABL_GROQ_KEY")
    if groq_key:
        providers["groq"] = OpenAICompatibleProvider(
            name="groq",
            api_key=groq_key,
            base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            model=os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
            timeout=float(os.getenv("AI_TIMEOUT", "30")),
        )
    moonshot_key = os.getenv("MOONSHOT_API_KEY") or os.getenv("HEABL_MOONSHOT_KEY")
    if moonshot_key:
        providers["moonshot"] = OpenAICompatibleProvider(
            name="moonshot",
            api_key=moonshot_key,
            base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1"),
            model=os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k"),
            timeout=float(os.getenv("AI_TIMEOUT", "30")),
        )
    zhipu_key = os.getenv("ZHIPU_API_KEY") or os.getenv("HEABL_ZHIPU_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("HEABL_GEMINI_KEY")
    if gemini_key:
        providers["gemini"] = OpenAICompatibleProvider(
            name="gemini",
            api_key=gemini_key,
            base_url=os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
            model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            timeout=float(os.getenv("AI_TIMEOUT", "30")),
        )
    doubao_key = os.getenv("HEABL_DOUBAO_KEY")
    if doubao_key:
        providers["doubao"] = OpenAICompatibleProvider(
            name="doubao",
            api_key=doubao_key,
            base_url=os.getenv("HEABL_DOUBAO_BASE", "https://ark.cn-beijing.volces.com/api/v3"),
            model=os.getenv("HEABL_DOUBAO_MODEL", "ep-202406140015"),
            timeout=float(os.getenv("AI_TIMEOUT", "30")),
        )
    coolyeah_key = os.getenv("HEABL_COOLYEAH_KEY")
    if coolyeah_key:
        providers["coolyeah"] = OpenAICompatibleProvider(
            name="coolyeah",
            api_key=coolyeah_key,
            base_url=os.getenv("HEABL_COOLYEAH_BASE", "https://api.coolyeah.com/v1"),
            model=os.getenv("HEABL_COOLYEAH_MODEL", "gpt-4o-mini"),
            timeout=float(os.getenv("AI_TIMEOUT", "30")),
        )
    if zhipu_key:
        providers["zhipu"] = OpenAICompatibleProvider(
            name="zhipu",
            api_key=zhipu_key,
            base_url=os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
            model=os.getenv("ZHIPU_MODEL", "glm-4"),
            timeout=float(os.getenv("AI_TIMEOUT", "30")),
        )
    return providers

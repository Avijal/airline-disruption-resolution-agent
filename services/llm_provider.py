import os
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

# Automatically load .env if present
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
except ImportError:
    pass

logger = logging.getLogger("airline_resolution_agent.llm")


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, messages: List[Dict[str, str]], **kwargs) -> str:
        pass


class DeterministicFallbackProvider(BaseLLMProvider):
    """
    Guaranteed offline provider that synthesizes responses using deterministic
    rule templates and tone guidelines. Ensures 100% testability and zero downtime
    even without external API keys.
    """

    def generate(self, system_prompt: str, messages: List[Dict[str, str]], **kwargs) -> str:
        context = kwargs.get("resolution_context")
        if context:
            return self._format_from_context(context)
        last_msg = messages[-1]["content"] if messages else ""
        return f"Under our policy rules, your request regarding '{last_msg}' is being processed according to official service entitlements."

    def _format_from_context(self, ctx: Dict[str, Any]) -> str:
        status = ctx.get("status", "RESOLVED")
        decision_text = ctx.get("decision_summary", "")
        actions_text = ctx.get("actions_summary", "")
        escalation_text = ctx.get("escalation_summary", "")
        tone_ack = ctx.get("tone_acknowledgment", "")

        parts = []
        if tone_ack:
            parts.append(tone_ack)

        if decision_text:
            parts.append(decision_text)

        if actions_text:
            parts.append(actions_text)

        if status == "ESCALATED" and escalation_text:
            parts.append(escalation_text)

        return "\n\n".join(parts)


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    def generate(self, system_prompt: str, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            import httpx

            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            full_msgs = [{"role": "system", "content": system_prompt}] + messages
            payload = {
                "model": self.model,
                "messages": full_msgs,
                "temperature": 0.2
            }
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}. Falling back to deterministic provider.")
            return DeterministicFallbackProvider().generate(system_prompt, messages, **kwargs)


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model

    def generate(self, system_prompt: str, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            import httpx

            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            formatted_msgs = []
            for m in messages:
                if m["role"] in ["user", "assistant"]:
                    formatted_msgs.append({"role": m["role"], "content": m["content"]})
            payload = {
                "model": self.model,
                "system": system_prompt,
                "messages": formatted_msgs,
                "max_tokens": 1000,
                "temperature": 0.2
            }
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["content"][0]["text"]
        except Exception as e:
            logger.warning(f"Anthropic API call failed: {e}. Falling back to deterministic provider.")
            return DeterministicFallbackProvider().generate(system_prompt, messages, **kwargs)


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model or "gemini-1.5-flash"

    def generate(self, system_prompt: str, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            import httpx

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            contents = []
            if system_prompt:
                contents.append({"role": "user", "parts": [{"text": f"System Instructions: {system_prompt}"}]})
                contents.append({"role": "model", "parts": [{"text": "Understood. I will strictly follow these instructions and business policy constraints."}]})
            for m in messages:
                role = "user" if m["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m["content"]}]})
            payload = {"contents": contents}
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}. Falling back to deterministic provider.")
            return DeterministicFallbackProvider().generate(system_prompt, messages, **kwargs)


class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b"):
        self.api_key = api_key
        self.model = model or "openai/gpt-oss-120b"

    def generate(self, system_prompt: str, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            import httpx

            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            full_msgs = [{"role": "system", "content": system_prompt}] + messages
            payload = {
                "model": self.model,
                "messages": full_msgs,
                "temperature": 0.2
            }
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Groq API call failed: {e}. Falling back to deterministic provider.")
            return DeterministicFallbackProvider().generate(system_prompt, messages, **kwargs)


class XAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "grok-2-latest"):
        self.api_key = api_key
        self.model = model or "grok-2-latest"

    def generate(self, system_prompt: str, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            import httpx

            url = "https://api.x.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            full_msgs = [{"role": "system", "content": system_prompt}] + messages
            payload = {
                "model": self.model,
                "messages": full_msgs,
                "temperature": 0.2
            }
            with httpx.Client(timeout=15.0) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"xAI Grok API call failed: {e}. Falling back to deterministic provider.")
            return DeterministicFallbackProvider().generate(system_prompt, messages, **kwargs)


def get_llm_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> BaseLLMProvider:
    """
    Factory creating configured LLM provider.
    Checks arguments first, then environment variables, then defaults to deterministic fallback.
    """
    prov = (provider_name or os.getenv("LLM_PROVIDER", "deterministic")).strip().lower()
    key = (api_key if api_key is not None else os.getenv("LLM_API_KEY", "")).strip()
    mdl = (model or os.getenv("LLM_MODEL", "")).strip()

    if (prov in ["gemini", "google"]) and key:
        return GeminiProvider(api_key=key, model=mdl or "gemini-1.5-flash")
    elif prov == "openai" and key:
        return OpenAIProvider(api_key=key, model=mdl or "gpt-4o")
    elif prov == "anthropic" and key:
        return AnthropicProvider(api_key=key, model=mdl or "claude-3-5-sonnet-20241022")
    elif prov == "groq" and key:
        return GroqProvider(api_key=key, model=mdl or "llama-3.3-70b-versatile")
    elif prov in ["grok", "xai"] and key:
        return XAIProvider(api_key=key, model=mdl or "grok-2-latest")

    return DeterministicFallbackProvider()

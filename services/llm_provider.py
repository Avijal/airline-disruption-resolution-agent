import os
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

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
        # If context was injected via kwargs or system_prompt, use it
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
        self.model = model

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


def get_llm_provider() -> BaseLLMProvider:
    """Factory creating configured LLM provider from environment variables."""
    provider_name = os.getenv("LLM_PROVIDER", "deterministic").strip().lower()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "")

    if provider_name == "openai" and api_key:
        return OpenAIProvider(api_key=api_key, model=model or "gpt-4o")
    elif provider_name == "anthropic" and api_key:
        return AnthropicProvider(api_key=api_key, model=model or "claude-3-5-sonnet-20241022")
    elif provider_name in ["gemini", "google"] and api_key:
        return GeminiProvider(api_key=api_key, model=model or "gemini-1.5-flash")

    return DeterministicFallbackProvider()

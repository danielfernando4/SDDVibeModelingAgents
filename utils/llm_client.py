"""
Cliente LLM multi-proveedor.
OpenAI y DeepSeek: AsyncOpenAI. Gemini: REST API nativa.
"""

import os
import httpx
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")

_openai_client = AsyncOpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None
_deepseek_client = AsyncOpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com/v1") if DEEPSEEK_KEY else None

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


async def call_llm(system_prompt: str, user_prompt: str, provider: str, model: str, api_key: str = "", **kwargs) -> str:
    text, _ = await _call_with_usage(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt or "Responde."}],
        provider, model,
    )
    return text


async def call_llm_with_history(messages: list[dict], provider: str, model: str, **kwargs) -> str:
    text, _ = await call_llm_with_history_and_usage(messages, provider, model, **kwargs)
    return text


async def call_llm_with_history_and_usage(messages: list[dict], provider: str, model: str, **kwargs) -> tuple[str, dict]:
    return await _call_with_usage(messages, provider, model)


async def _call_with_usage(messages: list[dict], provider: str, model: str) -> tuple[str, dict]:
    if provider == "gemini":
        return await _call_gemini_rest(messages, model)

    if provider == "deepseek":
        client = _deepseek_client or AsyncOpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com/v1")
    else:
        client = _openai_client or AsyncOpenAI(api_key=OPENAI_KEY)

    response = await client.chat.completions.create(model=model, messages=messages, temperature=0.3)
    usage = {}
    if response.usage:
        usage = {"input_tokens": response.usage.prompt_tokens or 0, "output_tokens": response.usage.completion_tokens or 0, "total_tokens": response.usage.total_tokens or 0}
    return response.choices[0].message.content, usage


async def _call_gemini_rest(messages: list[dict], model: str) -> tuple[str, dict]:
    system_parts = []
    contents = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            system_parts.append(content)
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
        else:
            contents.append({"role": "user", "parts": [{"text": content}]})

    if system_parts and contents:
        contents[0]["parts"].insert(0, {"text": "\n\n".join(system_parts) + "\n\n"})

    body = {"contents": contents}
    if len(contents) > 1:
        body["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]} if system_parts and len(contents) > 1 else None
        if body["systemInstruction"] is None:
            body.pop("systemInstruction", None)

    url = f"{GEMINI_BASE}/{model}:generateContent?key={GEMINI_KEY}"
    async with httpx.AsyncClient(timeout=120) as http:
        resp = await http.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()

    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    usage_meta = data.get("usageMetadata", {})
    usage = {
        "input_tokens": usage_meta.get("promptTokenCount", 0),
        "output_tokens": usage_meta.get("candidatesTokenCount", 0),
        "total_tokens": usage_meta.get("totalTokenCount", 0),
    }
    return text, usage

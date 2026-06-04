from openai import AsyncOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL

_async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def call_llm(system_prompt: str, user_prompt: str, model: str | None = None) -> str:
    effective_model = model or OPENAI_MODEL
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt or "Responde según las instrucciones del system prompt."},
    ]
    response = await _async_client.chat.completions.create(
        model=effective_model,
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content


async def call_llm_with_history(messages: list[dict], model: str | None = None) -> str:
    effective_model = model or OPENAI_MODEL
    response = await _async_client.chat.completions.create(
        model=effective_model,
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content

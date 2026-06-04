"""
LLM client — unified interface for calling language models.

Uses the observability module's factory to get an instrumented or standard
AsyncOpenAI client. Passes session/user/trace metadata to the client so
that Langfuse can group and attribute calls correctly.

When Langfuse is disabled, extra kwargs are filtered out before the call.
"""

from observability import create_llm_client, is_enabled
from config import OPENAI_MODEL

_async_client = None


def _get_client():
    """Lazy-init the AsyncOpenAI client (instrumented or standard)."""
    global _async_client
    if _async_client is None:
        _async_client = create_llm_client()
    return _async_client


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    trace_id: str | None = None,
    parent_observation_id: str | None = None,
    trace_name: str | None = None,
) -> str:
    effective_model = model or OPENAI_MODEL
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt or "Responde según las instrucciones del system prompt."},
    ]

    kwargs = dict(model=effective_model, messages=messages, temperature=0.3)

    if is_enabled():
        if trace_id:
            kwargs["trace_id"] = trace_id
        if parent_observation_id:
            kwargs["parent_observation_id"] = parent_observation_id
        if trace_name:
            kwargs["name"] = trace_name

    response = await _get_client().chat.completions.create(**kwargs)
    return response.choices[0].message.content


async def call_llm_with_history(
    messages: list[dict],
    model: str | None = None,
    trace_id: str | None = None,
    parent_observation_id: str | None = None,
    trace_name: str | None = None,
) -> str:
    effective_model = model or OPENAI_MODEL

    kwargs = dict(model=effective_model, messages=messages, temperature=0.3)

    if is_enabled():
        if trace_id:
            kwargs["trace_id"] = trace_id
        if parent_observation_id:
            kwargs["parent_observation_id"] = parent_observation_id
        if trace_name:
            kwargs["name"] = trace_name

    response = await _get_client().chat.completions.create(**kwargs)
    return response.choices[0].message.content

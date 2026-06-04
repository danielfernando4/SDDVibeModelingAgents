"""
LLM client factory — returns an instrumented or standard AsyncOpenAI client.

When Langfuse is enabled, uses the langfuse.openai drop-in wrapper that
automatically traces all OpenAI API calls (tokens, costs, latency).
When disabled, uses the standard openai.AsyncOpenAI client.

This factory is the single point to swap LLM providers in the future.
"""

from __future__ import annotations

from config import OPENAI_API_KEY


def create_llm_client():
    """
    Factory that returns an AsyncOpenAI client.

    If Langfuse is enabled and available, returns the instrumented wrapper
    from langfuse.openai. Otherwise, returns the standard openai client.
    """
    from observability.tracker import is_enabled, get_langfuse_client

    if is_enabled() and get_langfuse_client() is not None:
        try:
            from langfuse.openai import AsyncOpenAI
            return AsyncOpenAI(api_key=OPENAI_API_KEY)
        except ImportError:
            pass

    from openai import AsyncOpenAI
    return AsyncOpenAI(api_key=OPENAI_API_KEY)

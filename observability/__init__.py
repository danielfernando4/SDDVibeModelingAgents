"""
Observability module — Langfuse integration for SDDVibeModelingAgents.

This module encapsulates all monitoring/tracing logic. The rest of the
application imports only from this package, never directly from langfuse.

To swap the monitoring provider in the future, modify only this package.

Public API:
    - is_enabled()        → bool: check if monitoring is active
    - create_trace(...)   → trace object or None
    - create_llm_client() → AsyncOpenAI (instrumented or standard)
    - generate_session_id(spec_name) → str
    - flush()             → ensure all events are sent
    - shutdown()          → flush + cleanup
"""

from observability.tracker import (
    is_enabled,
    get_langfuse_client,
    create_trace,
    observability_context,
    flush,
    shutdown,
)
from observability.llm_wrapper import create_llm_client
from observability.session import generate_session_id

__all__ = [
    "is_enabled",
    "get_langfuse_client",
    "create_trace",
    "observability_context",
    "create_llm_client",
    "generate_session_id",
    "flush",
    "shutdown",
]

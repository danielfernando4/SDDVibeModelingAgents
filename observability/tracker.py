"""
Langfuse observability tracker â€” singleton client and trace management.

Langfuse v4 (OTEL-based) removed the legacy v2 API (client.trace(), etc.).
In v4 the correct imperative API is:

    span = client.start_observation(name=..., as_type="span", ...)
    # ... do work ...
    span.update(output=..., metadata=...)
    span.end()

session_id and user_id are passed via the langfuse_session_id /
langfuse_user_id kwargs directly on each OpenAI .create() call (handled
by the langfuse.openai wrapper). The root span groups all child generations.

This module provides:
  - get_langfuse_client()  â†’ singleton with auth check
  - is_enabled()           â†’ bool
  - create_trace()         â†’ _TraceHandle (safe .update()/.end() wrapper)
  - flush() / shutdown()   â†’ lifecycle
"""

from __future__ import annotations



from config import (
    LANGFUSE_SECRET_KEY,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_HOST,
    LANGFUSE_USER_ID,
)

_client = None
_initialized = False


# â”€â”€ Lightweight handle returned by create_trace() â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class _TraceHandle:
    """
    Wraps a Langfuse v4 span so callers can safely call .update() and .end().
    When Langfuse is unavailable _span is None and all calls are silent no-ops.
    """

    def __init__(self, span=None):
        self._span = span

    @property
    def id(self) -> str | None:
        return self._span.id if self._span else None

    @property
    def trace_id(self) -> str | None:
        return self._span.trace_id if self._span else None

    def update(self, output=None, metadata=None, **kwargs):
        if self._span is None:
            return
        try:
            self._span.update(
                output=output,
                metadata=metadata,
                **{k: v for k, v in kwargs.items()},
            )
        except Exception:
            pass

    def end(self):
        if self._span is None:
            return
        try:
            self._span.end()
        except Exception:
            pass


# â”€â”€ Client management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _has_credentials() -> bool:
    """Check if Langfuse credentials are set in environment variables."""
    return bool(LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY)


def is_enabled() -> bool:
    """Check if Langfuse credentials are configured and connection is active."""
    return get_langfuse_client() is not None


def get_langfuse_client():
    """
    Get or create the singleton Langfuse client.
    Returns None if credentials are not configured or auth fails.
    """
    global _client, _initialized

    if _initialized:
        return _client

    _initialized = True

    if not _has_credentials():
        _client = None
        return None

    try:
        from langfuse import Langfuse

        _client = Langfuse(
            secret_key=LANGFUSE_SECRET_KEY,
            public_key=LANGFUSE_PUBLIC_KEY,
            host=LANGFUSE_HOST,
        )
        try:
            auth_ok = _client.auth_check()
        except Exception as auth_err:
            print(f"  [!] Langfuse: auth_check fallo ({type(auth_err).__name__}), monitoreo deshabilitado")
            _client = None
            return _client

        if auth_ok:
            print("  [OK] Langfuse: conectado")
        else:
            print("  [!] Langfuse: credenciales invalidas, monitoreo deshabilitado")
            _client = None
    except Exception as e:
        print(f"  [!] Langfuse: error al conectar ({type(e).__name__}), monitoreo deshabilitado")
        _client = None

    return _client


# â”€â”€ Context manager for trace attribute propagation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class _ObservabilityContext:
    """Class-based context manager to avoid generator throw() issues with @contextmanager."""

    def __init__(self, session_id: str | None = None, user_id: str | None = None):
        self._session_id = session_id
        self._user_id = user_id
        self._cm = None

    def __enter__(self):
        if is_enabled():
            try:
                from langfuse import propagate_attributes
                self._cm = propagate_attributes(session_id=self._session_id, user_id=self._user_id)
                self._cm.__enter__()
            except Exception:
                self._cm = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._cm is not None:
            try:
                self._cm.__exit__(exc_type, exc_val, exc_tb)
            except Exception:
                pass
        return False


def observability_context(session_id: str | None = None, user_id: str | None = None):
    return _ObservabilityContext(session_id=session_id, user_id=user_id)


# â”€â”€ Trace creation (v4 imperative API) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_trace(
    name: str,
    session_id: str | None = None,
    user_id: str | None = None,
    metadata: dict | None = None,
    tags: list[str] | None = None,
    input: dict | str | None = None,
) -> _TraceHandle:
    """
    Create a root span for a flow execution using the Langfuse v4 API.

    Uses client.start_observation(as_type="span") â€” the v4 imperative call
    that returns a LangfuseSpan with .update() and .end() methods.

    session_id and user_id are embedded in metadata because the v4 span API
    does not expose them as top-level parameters (they are propagated via
    OTEL context or via langfuse_* kwargs on individual OpenAI .create() calls).

    Returns a _TraceHandle that is always safe to call â€” it degrades to a
    no-op when Langfuse is unavailable.
    """
    client = get_langfuse_client()
    if not client:
        return _TraceHandle(None)

    try:
        effective_user = user_id or LANGFUSE_USER_ID
        combined_metadata: dict = {}

        if session_id:
            combined_metadata["session_id"] = session_id
        if effective_user:
            combined_metadata["user_id"] = effective_user
        if tags:
            combined_metadata["tags"] = tags
        if metadata:
            combined_metadata.update(metadata)

        span = client.start_observation(
            name=name,
            as_type="span",
            input=input,
            metadata=combined_metadata if combined_metadata else None,
        )
        return _TraceHandle(span)

    except Exception as e:
        # Non-fatal: tracing is best-effort
        return _TraceHandle(None)


# â”€â”€ Lifecycle â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def flush() -> None:
    """Flush all pending Langfuse events. Call before exiting."""
    if _client is not None:
        try:
            _client.flush()
        except Exception:
            pass


def shutdown() -> None:
    """Flush and shutdown the Langfuse client."""
    global _client, _initialized
    if _client is not None:
        try:
            _client.shutdown()
        except Exception:
            pass
    _client = None
    _initialized = False
# --- Agent observation (v4 imperative API) ---

class _ObservedCall:
    """Wraps an LLM call with Langfuse observation (generation span)."""

    def __init__(self, name: str, provider: str, model: str, input_data=None):
        self._handle = None
        if is_enabled():
            try:
                client = get_langfuse_client()
                self._handle = client.start_observation(
                    name=name, as_type="generation", model=model,
                    input=input_data, metadata={"provider": provider},
                )
            except Exception:
                self._handle = None

    def end(self, output=None, usage=None):
        if self._handle is not None:
            try:
                kwargs = {}
                if output: kwargs["output"] = str(output)[:2000]
                if usage: kwargs["usage"] = usage
                if kwargs: self._handle.update(**kwargs)
                self._handle.end()
            except Exception:
                pass

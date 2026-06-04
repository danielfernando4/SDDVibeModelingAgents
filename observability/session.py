"""
Session management for observability.

Generates unique session IDs that group all interactions within a single
CLI execution. Sessions appear in the Langfuse dashboard as a way to
see all traces from one user session together.
"""

from __future__ import annotations

from datetime import datetime


def generate_session_id(spec_name: str) -> str:
    """
    Generate a unique session ID for a CLI execution.

    Format: sdd-{spec_name}-{YYYYMMDD-HHMMSS}
    Example: sdd-demo-20260603-213702
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"sdd-{spec_name}-{timestamp}"

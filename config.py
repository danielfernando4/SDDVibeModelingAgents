import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
SPECS_DIRECTORY = PROJECT_ROOT / "specs"
PROMPTS_DIRECTORY = PROJECT_ROOT / "prompts"
QUALITY_CRITERIA_DIRECTORY = PROJECT_ROOT / "quality_criteria"
TEMPLATES_DIRECTORY = PROJECT_ROOT / "templates"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Langfuse observability
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com"
LANGFUSE_USER_ID = os.getenv("LANGFUSE_USER_ID", "anonymous")

DEFAULT_SPEC_NAME = "demo"

MAX_ITERATIONS_PRODUCT = 4
MAX_ITERATIONS_REQUIREMENTS = 4
MAX_ITERATIONS_DESIGN = 5

# ── Agent names in Langfuse ─────────────────────────────────────────────────
# These names appear in the Langfuse dashboard for each trace/generation.
# Edit freely — they have no effect on the agent logic itself.
AGENT_NAMES = {
    # Root trace created per user-initiated flow
    "product_trace":           "ProductFlow",
    "requirements_trace":      "RequirementsFlow",
    "design_trace":            "DesignFlow",

    # Prompt clarification step (one per flow, before the creator loop)
    "product_clarify":         "ProductClarifier",
    "requirements_clarify":    "RequirementsClarifier",
    "design_clarify":          "DesignClarifier",

    # Creator agents (generate/refine the document)
    "product_creator":         "ProductCreator",
    "requirements_creator":    "RequirementsCreator",
    "design_creator":          "DesignCreator",

    # Reviewer agents (evaluate quality and produce redirection_summary)
    "product_reviewer":        "ProductReviewer",
    "requirements_reviewer":   "RequirementsReviewer",
    "design_reviewer":         "DesignReviewer",
}

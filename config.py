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

DEFAULT_SPEC_NAME = "demo"

MAX_ITERATIONS_PRODUCT = 4
MAX_ITERATIONS_REQUIREMENTS = 4
MAX_ITERATIONS_DESIGN = 5

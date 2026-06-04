"""
Configuración de agentes LLM. Permite asignar proveedor y modelo a cada agente.

Formato: {"agent_name": {"provider": "openai|gemini|deepseek", "model": "..."}}

Usar la opción 5 del menú para cargar los defaults.
Usar la opción 6 para configurar cada agente manualmente.
"""

import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "agent_config.json"

DEFAULTS = {
    "product_creator":      {"provider": "deepseek",  "model": "deepseek-chat"},
    "product_reviewer":     {"provider": "deepseek",  "model": "deepseek-chat"},
    "requirements_creator": {"provider": "deepseek",  "model": "deepseek-chat"},
    "requirements_reviewer":{"provider": "openai",    "model": "gpt-4o-mini"},
    "design_creator":       {"provider": "deepseek",  "model": "deepseek-chat"},
    "design_reviewer":      {"provider": "openai",    "model": "gpt-4o-mini"},
    "clarifier":            {"provider": "openai",    "model": "gpt-4o-mini"},
}

_current_config: dict | None = None


def load_defaults():
    """Carga la configuración por defecto y la guarda en disco."""
    global _current_config
    _current_config = dict(DEFAULTS)
    _save_to_disk()


def load_from_disk() -> dict:
    """Carga la configuración desde el archivo JSON."""
    global _current_config
    if CONFIG_FILE.exists():
        try:
            _current_config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return _current_config
        except (json.JSONDecodeError, KeyError):
            pass
    _current_config = dict(DEFAULTS)
    return _current_config


def _save_to_disk():
    if _current_config:
        CONFIG_FILE.write_text(json.dumps(_current_config, indent=2), encoding="utf-8")


def get_agent_config(agent_name: str) -> dict:
    """Devuelve {provider, model} para un agente específico."""
    global _current_config
    if _current_config is None:
        load_from_disk()
    return _current_config.get(agent_name, {"provider": "openai", "model": "gpt-4o-mini"})


def set_agent_config(agent_name: str, provider: str, model: str):
    """Configura un agente individual."""
    global _current_config
    if _current_config is None:
        load_from_disk()
    _current_config[agent_name] = {"provider": provider, "model": model}
    _save_to_disk()


def get_all_agents() -> list:
    """Devuelve lista de nombres de agentes configurables (excluye clarifier)."""
    return [name for name in DEFAULTS.keys() if name != "clarifier"]


def get_current_config() -> dict:
    """Devuelve la configuración actual completa."""
    global _current_config
    if _current_config is None:
        load_from_disk()
    return dict(_current_config)

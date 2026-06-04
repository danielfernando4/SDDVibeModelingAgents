"""
Flow Agent - SDD con LangGraph

Ejecuta: python main.py [spec_name]

Menú interactivo: 1.Producto  2.Requisitos  3.Diseño
"""

import sys
import asyncio
import traceback
from pathlib import Path

# Force stdout/stderr to UTF-8 to prevent UnicodeEncodeError on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import SPECS_DIRECTORY, DEFAULT_SPEC_NAME, LANGFUSE_USER_ID, AGENT_NAMES
from agent_config import load_defaults, get_all_agents, get_current_config, set_agent_config
from graph_builder import build_graph
from state import AgentState
from utils.llm_client import call_llm
from observability import (
    generate_session_id,
    create_trace,
    observability_context,
    flush as flush_observability,
    shutdown as shutdown_observability,
    is_enabled as observability_enabled,
)


def check_api_key() -> str | None:
    from config import OPENAI_API_KEY
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-tu-api"):
        return "OPENAI_API_KEY no configurada en .env"
    return None


def spec_file_exists(filepath: Path) -> bool:
    try:
        return filepath.exists() and filepath.read_text(encoding="utf-8").strip() != ""
    except Exception:
        return False


def build_status_line(spec_name: str) -> str:
    product_ok = spec_file_exists(SPECS_DIRECTORY / spec_name / "product.md")
    requirements_ok = spec_file_exists(SPECS_DIRECTORY / spec_name / "requirements.md")
    design_ok = spec_file_exists(SPECS_DIRECTORY / spec_name / "design.py")
    p = "✓" if product_ok else "✗"
    r = "✓" if requirements_ok else "✗"
    d = "✓" if design_ok else "✗"
    return f"P:{p} R:{r} D:{d}"


def can_access_phase(phase: str, spec_name: str) -> bool:
    if phase == "requirements":
        return spec_file_exists(SPECS_DIRECTORY / spec_name / "product.md")
    if phase == "design":
        return (
            spec_file_exists(SPECS_DIRECTORY / spec_name / "product.md")
            and spec_file_exists(SPECS_DIRECTORY / spec_name / "requirements.md")
        )
    return True  # product always accessible


MENU_TEMPLATE = """
  ┌──────────────────────────────────────────────┐
  │  1. Producto      [{product_marker}] visión, público, valor    │
  │  2. Requisitos    [{requirements_marker}] funcionalidad, EARS  │
  │  3. Diseño        [{design_marker}] diagrama de clases         │
  │                                              │
  │  0. Salir                                    │
  └──────────────────────────────────────────────┘

  ── Configuración de agentes ──
  5. Cargar configuración por defecto
  6. Configurar agentes individualmente"""


def build_menu(spec_name: str) -> str:
    product_ok = spec_file_exists(SPECS_DIRECTORY / spec_name / "product.md")
    requirements_ok = spec_file_exists(SPECS_DIRECTORY / spec_name / "requirements.md")
    design_ok = spec_file_exists(SPECS_DIRECTORY / spec_name / "design.py")

    can_req = product_ok
    can_des = product_ok and requirements_ok

    return MENU_TEMPLATE.format(
        product_marker="✓" if product_ok else " ",
        requirements_marker="✓" if requirements_ok else (" " if can_req else "✗"),
        design_marker="✓" if design_ok else (" " if can_des else "✗"),
    )


async def run_flow(prompt: str, target_phase: str, spec_name: str, session_id: str = ""):
    graph = build_graph().compile()

    spec_directory = SPECS_DIRECTORY / spec_name
    product_path = spec_directory / "product.md"
    requirements_path = spec_directory / "requirements.md"
    design_path = spec_directory / "design.py"

    user_id = LANGFUSE_USER_ID

    with observability_context(session_id=session_id, user_id=user_id):
        # Create a root trace for this flow execution
        trace = create_trace(
            name=AGENT_NAMES.get(f"{target_phase}_trace", f"{target_phase}-flow"),
            session_id=session_id,
            user_id=user_id,
            tags=[f"phase:{target_phase}", f"spec:{spec_name}"],
            input={"prompt": prompt, "target_phase": target_phase, "spec_name": spec_name},
        )

        initial_state: AgentState = {
            "messages": [],
            "user_prompt": prompt,
            "is_redirection": False,
            "redirection_source": None,
            "product_content": product_path.read_text(encoding="utf-8") if product_path.exists() else "",
            "requirements_content": requirements_path.read_text(encoding="utf-8") if requirements_path.exists() else "",
            "design_content": design_path.read_text(encoding="utf-8") if design_path.exists() else "",
            "product_exists": spec_file_exists(product_path),
            "requirements_exists": spec_file_exists(requirements_path),
            "design_exists": spec_file_exists(design_path),
            "redirection_queue": [],
            "current_redirection": None,
            "target_phase": target_phase,
            "spec_name": spec_name,
            "spec_directory": str(spec_directory),
            "session_id": session_id,
            "user_id": user_id,
            "trace_id": trace.trace_id or "",
            "parent_observation_id": trace.id or "",
        }

        await graph.ainvoke(initial_state)

        # Update and close the root trace span
        trace.update(output={"status": "completed", "specs_status": build_status_line(spec_name)})
        trace.end()


async def interactive_loop():
    spec_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SPEC_NAME

    api_error = check_api_key()
    if api_error:
        print(f"\n  ✗ ERROR: {api_error}")
        print("  Edita proyecto_flujo_agente/.env y agrega tu OPENAI_API_KEY\n")
        return

    # Initialize observability session
    session_id = generate_session_id(spec_name)
    obs_status = "ON" if observability_enabled() else "OFF"

    print(f"\n  FLOW AGENT - SDD  |  spec: {spec_name}  [{build_status_line(spec_name)}]")
    print(f"  Observability: {obs_status}  |  user: {LANGFUSE_USER_ID}  |  session: {session_id}")

    while True:
        print(build_menu(spec_name))

        try:
            choice = input("  Fase > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            break

        if choice == "0":
            print("  ¡Hasta luego!\n")
            break

        if choice == "5":
            load_defaults()
            print("\n  ✓ Configuración por defecto cargada:")
            _print_current_config()
            continue

        if choice == "6":
            await _configure_agents_interactively()
            continue

        if choice not in ("1", "2", "3"):
            print("  Opción no válida. Elige 1, 2, 3 o 0.\n")
            continue

        phase_map = {"1": "product", "2": "requirements", "3": "design"}
        target_phase = phase_map[choice]
        phase_labels = {"product": "Producto", "requirements": "Requisitos", "design": "Diseño"}
        phase_label = phase_labels[target_phase]

        if not can_access_phase(target_phase, spec_name):
            deps = {"requirements": "Producto", "design": "Producto y Requisitos"}
            dep_name = deps.get(target_phase, "")
            print(f"\n  ✗ No puedes ir a {phase_label}. {dep_name} debe existir primero.\n")
            continue

        try:
            prompt = input(f"  Prompt ({phase_label}) > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            break

        if not prompt:
            print("  Prompt vacío.\n")
            continue

        if prompt.lower() in ("salir", "exit", "quit", "q"):
            continue

        print(f"\n  → {phase_label}: \"{prompt[:100]}{'...' if len(prompt) > 100 else ''}\"")

        try:
            await run_flow(prompt, target_phase, spec_name, session_id=session_id)
        except Exception as error:
            tb = traceback.format_exc()
            error_type = type(error).__name__
            error_message = str(error) if str(error) else "(sin mensaje)"
            print(f"\n  ✗ ERROR [{error_type}]: {error_message}")
            for line in tb.split("\n")[-6:]:
                if line.strip():
                    print(f"  {line}")
            print()

        print(f"\n  [{build_status_line(spec_name)}]  Listo.\n")


def _print_current_config():
    config = get_current_config()
    for name in get_all_agents():
        cfg = config.get(name, {})
        print(f"    {name}: {cfg.get('provider', '?')}/{cfg.get('model', '?')}")
    print()


async def _configure_agents_interactively():
    import os as _os

    # ── Provider → Model catalogue ──────────────────────────────────────────
    PROVIDER_MODELS = {
        "openai":   ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1", "o4-mini"],
        "gemini":   ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"],
        "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    }

    # ── Detect which keys are present ───────────────────────────────────────
    _key_env = {
        "openai":   _os.getenv("OPENAI_API_KEY", ""),
        "gemini":   _os.getenv("GEMINI_API_KEY", ""),
        "deepseek": _os.getenv("DEEPSEEK_API_KEY", ""),
    }
    available_providers = [p for p, k in _key_env.items() if k and not k.startswith("sk-tu-api")]

    if not available_providers:
        print("\n  ✗ No hay API keys configuradas en .env")
        print("  Agrega al menos una: OPENAI_API_KEY, GEMINI_API_KEY o DEEPSEEK_API_KEY\n")
        return

    print("\n  ── Configurar agentes individualmente ──")
    print("  (presiona Enter para mantener el valor actual)\n")

    config = get_current_config()

    for name in get_all_agents():
        current = config.get(name, {})
        current_provider = current.get("provider", "openai")
        current_model = current.get("model", "gpt-4o-mini")
        print(f"  ╔══ Agente: {name}  [{current_provider}/{current_model}]")

        # ── Step 1: choose provider ─────────────────────────────────────────
        print("  ║  Escoja el proveedor:")
        for idx, prov in enumerate(available_providers, 1):
            marker = " ◀ actual" if prov == current_provider else ""
            print(f"  ║    {idx}. {prov}{marker}")
        print(f"  ║    0. Mantener actual ({current_provider})")

        try:
            prov_choice = input("  ║  Proveedor > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Configuración cancelada.\n")
            return

        if prov_choice == "" or prov_choice == "0":
            chosen_provider = current_provider
        elif prov_choice.isdigit() and 1 <= int(prov_choice) <= len(available_providers):
            chosen_provider = available_providers[int(prov_choice) - 1]
        else:
            print("  ║  ✗ Opción inválida, se mantiene el actual.")
            chosen_provider = current_provider

        # ── Step 2: choose model ────────────────────────────────────────────
        models = PROVIDER_MODELS.get(chosen_provider, [])
        if models:
            print(f"  ║  Modelos disponibles para {chosen_provider}:")
            for idx, mdl in enumerate(models, 1):
                marker = " ◀ actual" if mdl == current_model and chosen_provider == current_provider else ""
                print(f"  ║    {idx}. {mdl}{marker}")
            print(f"  ║    0. Mantener actual ({current_model})")

            try:
                model_choice = input("  ║  Modelo > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  Configuración cancelada.\n")
                return

            if model_choice == "" or model_choice == "0":
                chosen_model = current_model if chosen_provider == current_provider else models[0]
            elif model_choice.isdigit() and 1 <= int(model_choice) <= len(models):
                chosen_model = models[int(model_choice) - 1]
            else:
                print("  ║  ✗ Opción inválida, se usa el primero de la lista.")
                chosen_model = models[0]
        else:
            chosen_model = current_model

        set_agent_config(name, chosen_provider, chosen_model)
        print(f"  ╚══ ✓ {name} → {chosen_provider}/{chosen_model}\n")

    print("  ✓ Configuración guardada.\n")
    _print_current_config()


if __name__ == "__main__":
    try:
        asyncio.run(interactive_loop())
    finally:
        shutdown_observability()

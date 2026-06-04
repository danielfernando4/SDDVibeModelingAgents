"""
Flow Agent - SDD con LangGraph

Ejecuta: python main.py [spec_name]

Menú interactivo: 1.Producto  2.Requisitos  3.Diseño
"""

import sys
import asyncio
import traceback
from pathlib import Path

from config import SPECS_DIRECTORY, DEFAULT_SPEC_NAME
from graph_builder import build_graph
from state import AgentState
from utils.llm_client import call_llm


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
    design_ok = spec_file_exists(SPECS_DIRECTORY / spec_name / "design.json")
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
  └──────────────────────────────────────────────┘"""


def build_menu(spec_name: str) -> str:
    product_ok = spec_file_exists(SPECS_DIRECTORY / spec_name / "product.md")
    requirements_ok = spec_file_exists(SPECS_DIRECTORY / spec_name / "requirements.md")
    design_ok = spec_file_exists(SPECS_DIRECTORY / spec_name / "design.json")

    can_req = product_ok
    can_des = product_ok and requirements_ok

    return MENU_TEMPLATE.format(
        product_marker="✓" if product_ok else " ",
        requirements_marker="✓" if requirements_ok else (" " if can_req else "✗"),
        design_marker="✓" if design_ok else (" " if can_des else "✗"),
    )


async def run_flow(prompt: str, target_phase: str, spec_name: str):
    graph = build_graph().compile()

    spec_directory = SPECS_DIRECTORY / spec_name
    product_path = spec_directory / "product.md"
    requirements_path = spec_directory / "requirements.md"
    design_path = spec_directory / "design.json"

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
    }

    await graph.ainvoke(initial_state)


async def interactive_loop():
    spec_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SPEC_NAME

    api_error = check_api_key()
    if api_error:
        print(f"\n  ✗ ERROR: {api_error}")
        print("  Edita proyecto_flujo_agente/.env y agrega tu OPENAI_API_KEY\n")
        return

    print(f"\n  FLOW AGENT - SDD  |  spec: {spec_name}  [{build_status_line(spec_name)}]")

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
            await run_flow(prompt, target_phase, spec_name)
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


if __name__ == "__main__":
    asyncio.run(interactive_loop())

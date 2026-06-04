from pathlib import Path
from config import PROMPTS_DIRECTORY, QUALITY_CRITERIA_DIRECTORY, TEMPLATES_DIRECTORY
from utils.file_manager import read_file


def _join_sections(*sections: str) -> str:
    return "\n\n".join(section for section in sections if section)


def build_creator_system_prompt(phase: str, mode: str, state: dict) -> str:
    filename = f"creator_{mode}.md"
    base_prompt = read_file(PROMPTS_DIRECTORY / phase / filename)
    template = read_file(TEMPLATES_DIRECTORY / f"{phase}.md")

    prompt = _join_sections(base_prompt, template)

    if phase in ("requirements", "design"):
        product_content = state.get("product_content", "")
        if product_content:
            prompt = _join_sections(prompt, f"=== PRODUCTO (contexto de referencia) ===\n{product_content}")

    if phase == "design":
        requirements_content = state.get("requirements_content", "")
        if requirements_content:
            prompt = _join_sections(prompt, f"=== REQUISITOS (contexto de referencia) ===\n{requirements_content}")

    if mode in ("modify", "modify_redirection"):
        current_content = state.get(f"{phase}_content", "")
        if current_content:
            prompt = _join_sections(prompt, f"=== CONTENIDO ACTUAL A MODIFICAR ===\n{current_content}")

    if mode == "modify_redirection":
        redirection_feedback = state.get("current_redirection", {})
        source = redirection_feedback.get("source", "desconocido")
        summary = redirection_feedback.get("summary", "")
        suggestions = redirection_feedback.get("suggestions", "")
        prompt = _join_sections(
            prompt,
            f"=== REDIRECCIÓN DESDE {source.upper()} ===\n"
            f"Resumen de cambios en {source}: {summary}\n\n"
            f"Sugerencias para actualizar {phase}: {suggestions}\n\n"
            f"Aplica estos cambios al documento de {phase}."
        )

    return prompt


def build_reviewer_system_prompt(phase: str, mode: str, state: dict, creator_draft: str) -> str:
    filename = f"reviewer_{mode}.md"
    base_prompt = read_file(PROMPTS_DIRECTORY / phase / filename)

    quality_criteria = read_file(QUALITY_CRITERIA_DIRECTORY / f"{phase}.md")
    template = read_file(TEMPLATES_DIRECTORY / f"{phase}.md")

    prompt = _join_sections(base_prompt, quality_criteria, template)

    if mode != "create":
        previous_content = state.get(f"{phase}_content", "")
        if previous_content:
            prompt = _join_sections(prompt, f"=== CONTENIDO ANTERIOR (para comparar) ===\n{previous_content}")

    prompt = _join_sections(prompt, f"=== DRAFT A REVISAR ===\n{creator_draft}")

    if state.get("product_exists") and phase != "product":
        product_content = state.get("product_content", "")
        prompt = _join_sections(prompt, f"=== PRODUCTO (verificar coherencia) ===\n{product_content}")

    if state.get("requirements_exists") and phase != "requirements":
        requirements_content = state.get("requirements_content", "")
        prompt = _join_sections(prompt, f"=== REQUISITOS (verificar coherencia) ===\n{requirements_content}")

    if state.get("design_exists") and phase != "design":
        design_content = state.get("design_content", "")
        prompt = _join_sections(prompt, f"=== DISEÑO (verificar coherencia) ===\n{design_content}")

    user_prompt = state.get("user_prompt", "")
    if user_prompt:
        prompt = _join_sections(prompt, f"=== PROMPT ORIGINAL DEL USUARIO ===\n{user_prompt}")

    return prompt


def build_creator_user_message(phase: str, mode: str, state: dict) -> str:
    if mode == "create":
        return state.get("user_prompt", f"Genera el documento de {phase}.")

    if mode == "modify":
        return state.get("user_prompt", f"Modifica el documento de {phase} según la solicitud.")

    if mode == "modify_redirection":
        redirection_feedback = state.get("current_redirection", {})
        summary = redirection_feedback.get("summary", "")
        suggestions = redirection_feedback.get("suggestions", "")
        source = redirection_feedback.get("source", "otra fase")
        return (
            f"Recibiste una REDIRECCIÓN desde {source} con los siguientes cambios:\n\n"
            f"{summary}\n\n"
            f"Sugerencia: {suggestions}\n\n"
            f"Aplica los cambios necesarios al documento de {phase}. "
            f"Si consideras que estos cambios NO afectan a {phase}, "
            f"devuelve el documento SIN MODIFICAR."
        )

    return state.get("user_prompt", f"Genera el documento de {phase}.")

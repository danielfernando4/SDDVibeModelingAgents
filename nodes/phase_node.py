import json
import re
from pathlib import Path

from state import AgentState, RedirectionItem
from config import MAX_ITERATIONS_PRODUCT, MAX_ITERATIONS_REQUIREMENTS, MAX_ITERATIONS_DESIGN
from agents.prompt_builder import build_creator_system_prompt, build_reviewer_system_prompt, build_creator_user_message
from agents.creator import run_creator
from utils.file_manager import write_file
from utils.llm_client import call_llm_with_history, call_llm_with_history_and_usage
from observability.tracker import _ObservedCall
from agent_config import get_agent_config

ITERATIONS_MAP = {
    "product": MAX_ITERATIONS_PRODUCT,
    "requirements": MAX_ITERATIONS_REQUIREMENTS,
    "design": MAX_ITERATIONS_DESIGN,
}

PHASE_LABELS = {
    "product": "PRODUCTO",
    "requirements": "REQUISITOS",
    "design": "DISEÑO",
}

FILE_EXTENSIONS = {
    "product": "md",
    "requirements": "md",
    "design": "py",
}


async def _clarify_user_prompt(
    raw_prompt: str,
    phase: str,
    creator_system_prompt: str,
) -> str:
    clarification_prompt = (
        f"Analiza el siguiente prompt del usuario para la fase '{phase}' y detecta "
        f"ambigüedades o falta de claridad.\n\n"
        f"Prompt del usuario: \"{raw_prompt}\"\n\n"
        f"Si el prompt es CLARO, responde EXACTAMENTE: SIN_CAMBIOS\n"
        f"Si es AMBIGUO, reescríbelo de forma clara y precisa, resolviendo las "
        f"ambigüedades con interpretaciones razonables. No cambies la intención.\n\n"
        f"Responde SOLO con el prompt clarificado o SIN_CAMBIOS."
    )
    config = get_agent_config("clarifier")
    observation = _ObservedCall(
        name=f"{phase}-clarify", provider=config["provider"], model=config["model"],
        input_data=clarification_prompt[:500],
    )
    result_text, usage = await call_llm_with_history_and_usage(
        [{"role": "system", "content": creator_system_prompt}, {"role": "user", "content": clarification_prompt}],
        config["provider"], config["model"],
    )
    observation.end(output=result_text, usage=usage)
    result = result_text.strip()
    if result == "SIN_CAMBIOS":
        return raw_prompt
    return result


def _parse_review_json(raw_response: str) -> dict:
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", raw_response)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {"verdict": "APPROVED", "quality_score": 7}


def _strip_markdown_wrapper(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def _format_issue_list(issues: list) -> str:
    if not issues:
        return "Sin issues específicos."
    lines = []
    for i, issue in enumerate(issues, 1):
        severity = issue.get("severity", "P1")
        finding = issue.get("finding", "")
        fix = issue.get("fix", "")
        lines.append(f"{i}. [{severity}] {finding}\n   → {fix}")
    return "\n".join(lines)


async def run_phase_node(phase: str, state: AgentState) -> AgentState:
    label = PHASE_LABELS[phase]
    is_redirection = state.get("is_redirection", False)
    phase_exists = state.get(f"{phase}_exists", False)
    max_iterations = ITERATIONS_MAP[phase]

    if is_redirection:
        mode_label = "REDIRECCIÓN"
        creator_mode = "modify_redirection"
    elif not phase_exists:
        mode_label = "CREACIÓN"
        creator_mode = "create"
    else:
        mode_label = "MODIFICACIÓN"
        creator_mode = "modify"

    print(f"\n  ┌─ {label} [{mode_label}]")

    if is_redirection:
        redir_info = state.get("current_redirection", {})
        print(f"  │  origen redirección: {redir_info.get('source', '?')}")
        print(f"  │  resumen: {redir_info.get('summary', '')[:130]}")

    user_prompt_raw = state.get("user_prompt", "")
    if not is_redirection:
        creator_placeholder = build_creator_system_prompt(phase, creator_mode, state)
        clarified = await _clarify_user_prompt(
            user_prompt_raw, phase, creator_placeholder,
        )
        if clarified != user_prompt_raw:
            print(f"  │  prompt: \"{clarified[:120]}{'...' if len(clarified) > 120 else ''}\"")
        else:
            print(f"  │  prompt: \"{user_prompt_raw[:120]}{'...' if len(user_prompt_raw) > 120 else ''}\"")
        state["user_prompt"] = clarified
    else:
        print(f"  │  prompt: \"{user_prompt_raw[:120]}{'...' if len(user_prompt_raw) > 120 else ''}\"")

    # Build prompts
    creator_system = build_creator_system_prompt(phase, creator_mode, state)
    creator_message = build_creator_user_message(phase, creator_mode, state)

    reviewer_mode = "modify" if mode_label in ("MODIFICACIÓN", "REDIRECCIÓN") else "create"
    creator_cfg = get_agent_config(f"{phase}_creator")
    reviewer_cfg = get_agent_config(f"{phase}_reviewer")
    print(f"  │  creator: {creator_cfg['provider']}/{creator_cfg['model']} | creator_{creator_mode}.md")
    print(f"  │  reviewer: {reviewer_cfg['provider']}/{reviewer_cfg['model']} | reviewer_{reviewer_mode}.md")

    current_draft = ""
    reviewer_feedback_text = ""
    final_verdict = "NEEDS_REVISION"
    final_quality = 0
    last_review_data = {}

    for iteration_number in range(1, max_iterations + 1):
        creator_obs = _ObservedCall(
            name=f"{phase}-creator-{iteration_number}",
            provider=creator_cfg["provider"], model=creator_cfg["model"],
            input_data=creator_message[:500],
        )
        if iteration_number == 1:
            draft, usage = await run_creator(
                f"{phase}_creator", creator_system, creator_message,
            )
        else:
            refinement_message = (
                f"=== TAREAS PENDIENTES ===\n"
                f"Corrige CADA uno:\n\n{reviewer_feedback_text}\n\n"
                f"=== FIN TAREAS ===\n"
                f"Genera el documento COMPLETO. Conserva lo que no necesita cambios."
            )
            draft, usage = await run_creator(
                f"{phase}_creator", creator_system, creator_message,
                previous_draft=current_draft, reviewer_feedback=refinement_message,
            )
        creator_obs.end(output=draft[:500], usage=usage)

        current_draft = draft

        reviewer_system = build_reviewer_system_prompt(phase, reviewer_mode, state, draft)
        reviewer_config = get_agent_config(f"{phase}_reviewer")
        reviewer_obs = _ObservedCall(
            name=f"{phase}-reviewer-{iteration_number}",
            provider=reviewer_config["provider"], model=reviewer_config["model"],
            input_data=draft[:500],
        )
        review_result, review_usage = await call_llm_with_history_and_usage(
            [
                {"role": "system", "content": reviewer_system},
                {"role": "user", "content": (
                    f"Revisa este draft de {phase} (iteración {iteration_number}/{max_iterations}). "
                    f"Responde ÚNICAMENTE con el JSON de veredicto."
                )},
            ],
            reviewer_config["provider"], reviewer_config["model"],
        )
        reviewer_obs.end(output=review_result[:500], usage=review_usage)
        review_data = _parse_review_json(review_result)
        last_review_data = review_data
        final_verdict = review_data.get("verdict", "NEEDS_REVISION")
        final_quality = review_data.get("quality_score", "?")

        icon = "✓" if final_verdict == "APPROVED" else "↻"
        print(f"  │")
        print(f"  │  ── iteración {iteration_number}/{max_iterations} ──")
        print(f"  │  Creator → {len(draft)} caracteres")
        print(f"  │  Reviewer → {icon} {final_verdict} [{final_quality}/10]")

        if final_verdict == "APPROVED":
            if _draft_too_short(draft, phase, state):
                truncation_issue = {
                    "severity": "P0",
                    "finding": f"El documento generado ({len(draft)}c) es mucho más corto que el original ({len(state.get(f'{phase}_content', ''))}c). Se perdió contenido.",
                    "fix": "Genera el documento COMPLETO con TODAS las secciones. Solo modifica lo que el usuario pidió cambiar. Conserva el resto del contenido intacto."
                }
                review_data.setdefault("content_issues", []).append(truncation_issue)
                review_data["verdict"] = "NEEDS_REVISION"
                review_data["revision_instructions"] = "⚠️ EL DOCUMENTO ESTÁ TRUNCADO. Genera el documento COMPLETO conservando todo el contenido original y aplicando solo los cambios solicitados."
                final_verdict = "NEEDS_REVISION"
            else:
                break

        all_issues = (
            review_data.get("scope_decision_issues", [])
            + review_data.get("structural_issues", [])
            + review_data.get("content_issues", [])
            + review_data.get("cross_spec_issues", [])
        )
        revision_instructions = review_data.get("revision_instructions", "")

        if all_issues:
            print(f"  │")
            print(f"  │  Reviewer → Creator:")
            for issue in all_issues:
                severity = issue.get("severity", "?")
                finding = issue.get("finding", "")
                fix = issue.get("fix", "")
                print(f"  │    [{severity}] {finding}")
                if fix:
                    print(f"  │           → {fix[:130]}")
        if revision_instructions:
            print(f"  │")
            print(f"  │  Checklist:")
            if isinstance(revision_instructions, list):
                for line in revision_instructions[:6]:
                    print(f"  │    {line}")
            else:
                for line in str(revision_instructions).split("\n")[:6]:
                    if line.strip():
                        print(f"  │    {line.strip()}")

        if iteration_number == max_iterations:
            print(f"  │  ⚠ máximo iteraciones ({final_quality}/10), aceptando draft")
            break

        reviewer_feedback_text = revision_instructions if revision_instructions else _format_issue_list(all_issues)

    # Save to disk
    file_extension = FILE_EXTENSIONS[phase]
    filepath = Path(state["spec_directory"]) / f"{phase}.{file_extension}"
    current_draft = _strip_markdown_wrapper(current_draft)
    write_file(filepath, current_draft)

    state[f"{phase}_content"] = current_draft
    state[f"{phase}_exists"] = True

    print(f"  │  guardado: {phase}.{file_extension} ({len(current_draft)} caracteres)")

    # Extract redirection summary from reviewer's last response
    redirection_summary = _extract_redirection_summary(last_review_data, phase)
    if redirection_summary:
        print(f"  │  redirección: \"{redirection_summary[:150]}{'...' if len(redirection_summary) > 150 else ''}\"")
    await _handle_redirections(phase, state, redirection_summary, is_redirection, not phase_exists)

    # Status summary
    product_icon = "✓" if state.get("product_exists") else "✗"
    requirements_icon = "✓" if state.get("requirements_exists") else "✗"
    design_icon = "✓" if state.get("design_exists") else "✗"
    pending = len(state.get("redirection_queue", []))
    feedback_str = f"  cola: {pending}" if pending > 0 else ""
    print(f"  │  specs: P:{product_icon} R:{requirements_icon} D:{design_icon}{feedback_str}")
    print(f"  └{'─'*52}")

    state["target_phase"] = ""
    return state


async def _handle_redirections(
    phase: str,
    state: AgentState,
    redirection_summary: str,
    is_redirection: bool,
    is_first_creation: bool,
) -> None:
    if is_first_creation:
        print(f"  │  propagación: omitida (primera creación, sin versión anterior)")
        return

    if is_redirection:
        if phase in ("product", "design"):
            print(f"  │  propagación: omitida (nodo ejecutado por redirección)")
            return
        if phase == "requirements":
            redirection_source = state.get("redirection_source")
            reviewer_changes = redirection_summary if redirection_summary else f"Se modificaron requisitos."
            if redirection_source == "product" and state.get("design_exists"):
                print(f"  │  propagación: redirección desde producto → diseño")
                _add_to_redirection_queue(state, phase, "design",
                    reviewer_changes,
                    f"Revisar el diseño según los nuevos requisitos: {reviewer_changes}")
            elif redirection_source == "design":
                print(f"  │  propagación: redirección desde diseño → producto")
                _add_to_redirection_queue(state, phase, "product",
                    reviewer_changes,
                    f"Revisar producto según los nuevos requisitos: {reviewer_changes}")
            else:
                print(f"  │  propagación: sin fase destino para redirección")
        return

    if not redirection_summary or not redirection_summary.strip():
        print(f"  │  propagación: no requiere cambios en otras fases")
        return

    existing_phases = _get_existing_phases(state, phase)
    target_phases = _filter_propagation_targets(phase, existing_phases)
    if not target_phases:
        print(f"  │  propagación: sin fases destino según reglas de propagación")
        return

    for target_phase in target_phases:
        _add_to_redirection_queue(
            state, phase, target_phase,
            redirection_summary,
            f"Se modificó {phase}. Revisa si {target_phase} necesita actualizarse para reflejar: {redirection_summary}",
        )

    pending = len(state.get("redirection_queue", []))
    targets = ", ".join(sorted(target_phases))
    print(f"  │  propagación: {pending} redirección(es) → {targets}")


def _filter_propagation_targets(phase: str, existing_phases: set) -> set:
    if phase == "product":
        return {"requirements"} & existing_phases
    if phase == "design":
        return {"requirements"} & existing_phases
    if phase == "requirements":
        return existing_phases  # product (si existe) + design (si existe)
    return existing_phases


def _extract_redirection_summary(review_data: dict, phase: str) -> str:
    if not review_data:
        return ""
    summary = review_data.get("redirection_summary", "")
    if summary and isinstance(summary, str) and summary.strip():
        return summary.strip()
    return ""


def _draft_too_short(draft: str, phase: str, state: AgentState) -> bool:
    if not phase_exists_except(state, phase):
        return False
    previous = state.get(f"{phase}_content", "")
    if not previous or len(previous) < 500:
        return False
    if len(draft) < len(previous) * 0.5:
        return True
    return False


def _add_to_redirection_queue(state: AgentState, source: str, target: str, summary: str, suggestions: str) -> None:
    queue = state.get("redirection_queue", [])
    queue.append(RedirectionItem(
        source=source,
        target=target,
        summary=summary,
        suggestions=suggestions,
    ))
    state["redirection_queue"] = queue


def _get_existing_phases(state: AgentState, current_phase: str) -> set:
    phases = set()
    for phase_name in ["product", "requirements", "design"]:
        if phase_name != current_phase and state.get(f"{phase_name}_exists", False):
            phases.add(phase_name)
    return phases


def phase_exists_except(state: AgentState, current_phase: str) -> bool:
    for phase_name in ["product", "requirements", "design"]:
        if phase_name != current_phase and state.get(f"{phase_name}_exists", False):
            return True
    return False


# Convenience wrappers
async def product_node(state: AgentState) -> AgentState:
    return await run_phase_node("product", state)


async def requirements_node(state: AgentState) -> AgentState:
    return await run_phase_node("requirements", state)


async def design_node(state: AgentState) -> AgentState:
    return await run_phase_node("design", state)

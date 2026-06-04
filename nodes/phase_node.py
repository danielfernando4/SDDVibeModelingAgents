import json
import re
from pathlib import Path

from state import AgentState, RedirectionItem
from config import MAX_ITERATIONS_PRODUCT, MAX_ITERATIONS_REQUIREMENTS, MAX_ITERATIONS_DESIGN, AGENT_NAMES
from agents.prompt_builder import build_creator_system_prompt, build_reviewer_system_prompt, build_creator_user_message
from agents.creator import run_creator
from utils.file_manager import write_file
from utils.llm_client import call_llm_with_history

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
    "design": "json",
}


async def _clarify_user_prompt(
    raw_prompt: str,
    phase: str,
    creator_system_prompt: str,
    trace_id: str | None = None,
    parent_observation_id: str | None = None,
    trace_name: str | None = None,
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
    result = await call_llm_with_history(
        [
            {"role": "system", "content": creator_system_prompt},
            {"role": "user", "content": clarification_prompt},
        ],
        trace_id=trace_id,
        parent_observation_id=parent_observation_id,
        trace_name=trace_name or f"{phase}-clarify",
    )
    result = result.strip()
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


def _strip_json_wrapper(text: str) -> str:
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

    # Observability context
    session_id = state.get("session_id")
    user_id = state.get("user_id")
    trace_id = state.get("trace_id")
    parent_observation_id = state.get("parent_observation_id")

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
            trace_id=trace_id, parent_observation_id=parent_observation_id,
            trace_name=AGENT_NAMES.get(f"{phase}_clarify", f"{phase}-clarify"),
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
    print(f"  │  creator: creator_{creator_mode}.md  |  reviewer: reviewer_{reviewer_mode}.md")

    current_draft = ""
    reviewer_feedback_text = ""
    final_verdict = "NEEDS_REVISION"
    final_quality = 0
    last_review_data = {}

    for iteration_number in range(1, max_iterations + 1):
        if iteration_number == 1:
            draft = await run_creator(
                phase, creator_system, creator_message,
                trace_id=trace_id, parent_observation_id=parent_observation_id,
                trace_name=f"{AGENT_NAMES.get(f'{phase}_creator', f'{phase}-creator')}-iter{iteration_number}",
            )
        else:
            refinement_message = (
                f"=== TAREAS PENDIENTES ===\n"
                f"Corrige CADA uno:\n\n{reviewer_feedback_text}\n\n"
                f"=== FIN TAREAS ===\n"
                f"Genera el documento COMPLETO. Conserva lo que no necesita cambios."
            )
            draft = await run_creator(
                phase, creator_system, creator_message,
                previous_draft=current_draft, reviewer_feedback=refinement_message,
                trace_id=trace_id, parent_observation_id=parent_observation_id,
                trace_name=f"{AGENT_NAMES.get(f'{phase}_creator', f'{phase}-creator')}-iter{iteration_number}",
            )

        current_draft = draft

        reviewer_system = build_reviewer_system_prompt(phase, reviewer_mode, state, draft)
        review_result = await call_llm_with_history(
            [
                {"role": "system", "content": reviewer_system},
                {"role": "user", "content": (
                    f"Revisa este draft de {phase} (iteración {iteration_number}/{max_iterations}). "
                    f"Responde ÚNICAMENTE con el JSON de veredicto."
                )},
            ],
            trace_id=trace_id,
            parent_observation_id=parent_observation_id,
            trace_name=f"{AGENT_NAMES.get(f'{phase}_reviewer', f'{phase}-reviewer')}-iter{iteration_number}",
        )
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
    if phase == "design":
        current_draft = _strip_json_wrapper(current_draft)
    write_file(filepath, current_draft)

    state[f"{phase}_content"] = current_draft
    state[f"{phase}_exists"] = True

    print(f"  │  guardado: {phase}.{file_extension} ({len(current_draft)} caracteres)")

    # Extract redirection summary from reviewer's last response
    redirection_summary = _extract_redirection_summary(last_review_data, phase)
    if redirection_summary:
        print(f"  │  redirección: \"{redirection_summary[:150]}{'...' if len(redirection_summary) > 150 else ''}\"")
    await _handle_redirections(phase, state, redirection_summary, is_redirection)

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
) -> None:
    if is_redirection:
        if phase in ("product", "design"):
            print(f"  │  propagación: omitida (nodo ejecutado por redirección)")
            return
        if phase == "requirements":
            redirection_source = state.get("redirection_source")
            if redirection_source == "product" and state.get("design_exists"):
                print(f"  │  propagación: redirección desde producto → diseño")
                _add_to_redirection_queue(state, phase, "design",
                    f"Se modificaron requisitos por cambios en producto.",
                    f"Revisar el diseño según los nuevos requisitos.")
            elif redirection_source == "design":
                print(f"  │  propagación: redirección desde diseño → producto")
                _add_to_redirection_queue(state, phase, "product",
                    f"Se modificaron requisitos por cambios en diseño.",
                    f"Revisar producto según los nuevos requisitos.")
            else:
                print(f"  │  propagación: sin fase destino para redirección")
        return

    if not redirection_summary or not redirection_summary.strip():
        print(f"  │  propagación: no requiere cambios en otras fases")
        return

    existing_phases = _get_existing_phases(state, phase)
    if not existing_phases:
        print(f"  │  propagación: no hay otras fases existentes")
        return

    for target_phase in existing_phases:
        _add_to_redirection_queue(
            state, phase, target_phase,
            redirection_summary,
            f"Se modificó {phase}. Revisa si {target_phase} necesita actualizarse para reflejar: {redirection_summary}",
        )

    pending = len(state.get("redirection_queue", []))
    targets = ", ".join(sorted(existing_phases))
    print(f"  │  propagación: {pending} redirección(es) → {targets}")


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

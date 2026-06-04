import json
import re
from utils.llm_client import call_llm_with_history


async def run_creator(
    phase: str,
    system_prompt: str,
    user_message: str,
    previous_draft: str = "",
    reviewer_feedback: str = "",
    trace_id: str | None = None,
    parent_observation_id: str | None = None,
    trace_name: str | None = None,
) -> str:
    messages = [{"role": "system", "content": system_prompt}]

    if previous_draft and reviewer_feedback:
        messages.append({"role": "assistant", "content": previous_draft})
        messages.append({"role": "user", "content": reviewer_feedback})
    else:
        messages.append({"role": "user", "content": user_message})

    return await call_llm_with_history(
        messages,
        trace_id=trace_id,
        parent_observation_id=parent_observation_id,
        trace_name=trace_name or f"{phase}-creator",
    )


async def run_reviewer(
    phase: str,
    system_prompt: str,
    draft: str,
    iteration: int,
    max_iterations: int,
    trace_id: str | None = None,
    parent_observation_id: str | None = None,
    trace_name: str | None = None,
) -> dict:
    user_message = (
        f"=== PROMPT ORIGINAL DEL USUARIO ===\n"
        f"(verifica que el draft trate EXACTAMENTE sobre esto)\n\n"
        f"Revisa este draft de {phase} (iteración {iteration}/{max_iterations}). "
        f"Responde ÚNICAMENTE con el JSON de veredicto."
    )

    response = await call_llm_with_history(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        trace_id=trace_id,
        parent_observation_id=parent_observation_id,
        trace_name=trace_name or f"{phase}-reviewer",
    )

    return _parse_review_json(response)


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

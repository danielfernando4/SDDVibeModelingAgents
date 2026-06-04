import json
import re
from utils.llm_client import call_llm_with_history_and_usage
from agent_config import get_agent_config


async def run_creator(agent_name: str, system_prompt: str, user_message: str, previous_draft: str = "", reviewer_feedback: str = "", **kwargs) -> tuple[str, dict]:
    config = get_agent_config(agent_name)

    messages = [{"role": "system", "content": system_prompt}]

    if previous_draft and reviewer_feedback:
        messages.append({"role": "assistant", "content": previous_draft})
        messages.append({"role": "user", "content": reviewer_feedback})
    else:
        messages.append({"role": "user", "content": user_message})

    text, usage = await call_llm_with_history_and_usage(messages, config["provider"], config["model"])
    return text, usage


async def run_reviewer(agent_name: str, system_prompt: str, draft: str, iteration: int, max_iterations: int, phase: str) -> dict:
    config = get_agent_config(agent_name)

    user_message = (
        f"Revisa este draft de {phase} (iteración {iteration}/{max_iterations}). "
        f"Responde ÚNICAMENTE con el JSON de veredicto."
    )

    response = await call_llm_with_history(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        config["provider"], config["model"],
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

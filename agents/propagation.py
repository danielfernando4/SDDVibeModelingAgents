import json
import re
from utils.llm_client import call_llm_with_history
from utils.diff import extract_added_lines


async def analyze_propagation(
    phase: str,
    old_content: str,
    new_content: str,
    product_content: str,
    requirements_content: str,
    design_content: str,
) -> dict:
    added_text = extract_added_lines(old_content, new_content)
    if not added_text.strip():
        return {"changes_summary": "", "cross_phase_feedback": []}

    other_specs = ""
    if product_content and phase != "product":
        other_specs += f"\n=== PRODUCTO ===\n{product_content}\n"
    if requirements_content and phase != "requirements":
        other_specs += f"\n=== REQUISITOS ===\n{requirements_content}\n"
    if design_content and phase != "design":
        other_specs += f"\n=== DISEÑO ===\n{design_content}\n"

    system_prompt = (
        "Eres un analista de especificaciones SDD. Compara cambios y decide si otras fases necesitan actualizarse. "
        "Responde SOLO con JSON."
    )

    user_message = (
        f"Se hicieron cambios en {phase}. Analiza el contenido agregado y las otras especificaciones.\n\n"
        f"=== CONTENIDO AGREGADO EN {phase} ===\n{added_text}\n\n"
        f"=== OTRAS ESPECIFICACIONES ===\n{other_specs}\n\n"
        f"INSTRUCCIONES:\n"
        f"1. Identifica si el contenido agregado introduce NUEVA funcionalidad o entidades.\n"
        f"2. Para cada nueva funcionalidad, verifica en las otras especificaciones si YA está cubierta.\n"
        f"3. Si NO está cubierta → genera cross_phase_feedback con sugerencias concretas.\n"
        f"4. Si YA está cubierta → cross_phase_feedback vacío [].\n\n"
        f"Responde ÚNICAMENTE con JSON:\n"
        f'{{"changes_summary": "<resumen>", '
        f'"cross_phase_feedback": [{{"target_phase": "product|requirements|design", '
        f'"summary": "...", "suggestions": "...", "severity": "important|suggestion"}}]}}'
    )

    response = await call_llm_with_history(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
    )

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", response)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {"changes_summary": "", "cross_phase_feedback": []}

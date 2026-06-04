# Criterios de Calidad - Requisitos

## 0. Alineación con el Prompt (EVALUAR PRIMERO)
- ¿Los requisitos corresponden al producto/dominio que pidió el usuario?
- Si el usuario pidió "citas médicas" y hablan de "e-commerce", es P0.

## 0.5. Decisión de Scope
- ¿El cambio merece un NUEVO requisito? → Si tiene su propio "As a [ROL], I want [CAPACIDAD]" distinto.
- ¿El cambio merece un NUEVO criterio? → Si extiende una capacidad existente con variantes.
- ¿El cambio solo REFINA? → Modificar criterio existente.
- La mayoría de cambios serán NUEVOS CRITERIOS, no nuevos requisitos.

## 1. Estructural
- ¿Headings con ID numérico? (Requisito 1, Requisito 2...)
- ¿Cada requisito tiene al menos 1 criterio EARS?
- ¿EARS válido? When, If, While, Where + shall. Sujeto concreto.
- ¿Todo en español? Solo palabras clave EARS en inglés.
- ¿Sin lenguaje de implementación? (DB, frameworks, APIs)

## 2. Semántico / Contenido
- ¿Comportamiento OBSERVABLE y TESTABLE?
- ¿Cubre casos de error (no solo happy path)?
- ¿Sin ambigüedad? Términos como "rápido" necesitan métrica.
- ¿Reglas de negocio explícitas?

## 3. Consistencia Cross-Spec
- ¿Cada capability del producto tiene al menos un requisito?
- ¿Los roles de requisitos coinciden con el público objetivo del producto?

## FORMATO DE RESPUESTA (JSON)
{
  "verdict": "APPROVED" | "NEEDS_REVISION",
  "quality_score": <1 al 10>,
  "scope_decision_issues": [{"severity": "P0|P1|P2", "finding": "...", "fix": "..."}],
  "structural_issues": [{"severity": "P0|P1|P2", "finding": "...", "fix": "..."}],
  "content_issues": [{"severity": "P0|P1|P2", "finding": "...", "fix": "..."}],
  "cross_spec_issues": [{"severity": "P0|P1|P2", "finding": "...", "fix": "..."}],
  "revision_instructions": "<checklist numerado, una tarea por línea>",
  "redirection_summary": "<resumen de cambios para propagar a otras fases, o string vacío '' si no requiere propagación>"
}

## PROPAGACIÓN DE CAMBIOS
Al finalizar tu revisión, genera `redirection_summary`:
- Describe QUÉ cambió: "Se agregó Requisito 6 de facturación con 5 criterios EARS", "Se modificó el criterio 3 del Requisito 1".
- Si el cambio es cosmético o no introduce nueva funcionalidad → `redirection_summary: ""`.
- Si el cambio agrega nuevos requisitos o criterios significativos → escribe un resumen claro.
- NO incluyas sugerencias de qué hacer. Solo describe el cambio.

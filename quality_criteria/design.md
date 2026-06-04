# Criterios de Calidad - Diseño (Diagrama de Clases)

## 0. Alineación con el Prompt (EVALUAR PRIMERO)
- ¿El systemName y las clases corresponden al producto/dominio?
- ¿Cada clase está justificada por un requisito o el producto?

## 1. Estructural (Schema BUML)
- ¿JSON válido con systemName, classes[], relationships[]?
- ¿className PascalCase, UNA palabra, sin espacios ni tildes?
- ¿Mínimo 3 atributos por clase no-enum?
- ¿Enumerados con atributos solo "name" (sin type ni visibility)?
- ¿Tipos válidos: String, int, bool, float, boolean, Date, o nombre de clase/enum?
- ¿Parámetros de métodos: [{name, type}], NO strings?
- ¿Relaciones con type, source, target, sourceMultiplicity, targetMultiplicity?
- ¿NO campos position, x, y?
- ¿NO ```json ni bloques markdown?
- ¿NO clases huérfanas (sin relaciones)?
- ¿NO clases stub (1 solo atributo genérico)?

## 2. Semántico / Contenido
- ¿Clases representan entidades del dominio real? No técnicas (DatabaseManager, ApiController).
- ¿Relaciones con semántica correcta? Composición para "no existe sin", Herencia para "es-un".
- ¿Multiplicidades reflejan reglas de negocio?
- ¿Sin clases duplicadas o redundantes?
- ¿Todo en español?

## 3. Consistencia Cross-Spec
- ¿CADA requisito tiene clase/atributo/método/relación que lo satisface?
- ¿Capacidades del producto reflejadas en el diagrama?

## FORMATO DE RESPUESTA (JSON)
{
  "verdict": "APPROVED" | "NEEDS_REVISION",
  "quality_score": <1 al 10>,
  "structural_issues": [{"severity": "P0|P1|P2", "finding": "...", "fix": "..."}],
  "content_issues": [{"severity": "P0|P1|P2", "finding": "...", "fix": "..."}],
  "cross_spec_issues": [{"severity": "P0|P1|P2", "finding": "...", "fix": "..."}],
  "revision_instructions": "<checklist numerado, una tarea por línea>",
  "redirection_summary": "<resumen de cambios para propagar a otras fases, o string vacío '' si no requiere propagación>"
}

## PROPAGACIÓN DE CAMBIOS
Al finalizar tu revisión, genera `redirection_summary`:
- Describe QUÉ cambió: "Se agregó la clase Prescripcion con 3 atributos y relación con CitaMedica".
- Si el cambio es cosmético o no introduce nuevas entidades → `redirection_summary: ""`.
- Si el cambio agrega nuevas clases/entidades de dominio → escribe un resumen claro.
- NO incluyas sugerencias. Solo describe el cambio.

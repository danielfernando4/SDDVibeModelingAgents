# Criterios de Calidad - Producto

## 0. Alineación con el Prompt (EVALUAR PRIMERO)
- ¿El producto descrito corresponde EXACTAMENTE a lo que pidió el usuario?
- Si el usuario pidió "citas médicas" y el draft habla de "gestión de proyectos", es P0.

## 1. Estructural
- ¿Tiene TODAS las secciones requeridas? (Resumen Ejecutivo, Problema, Público Objetivo, Propuesta de Valor, Capacidades Clave, Casos de Uso, Alcance, Métricas, Restricciones)
- ¿El Alcance incluye "Dentro del Alcance", "Fuera del Alcance" y "Supuestos y Dependencias"?
- **⚠️ ¿El draft está TRUNCADO?** Si es mucho más corto que el original y perdió secciones completas, es P0. No apruebes un documento donde se perdieron secciones enteras.
- ¿Sin placeholders vacíos (TBD, [completar])?

## 2. Semántico / Contenido
- ¿Capacidades Clave son DIFERENCIADORAS (no genéricas como "login", "interfaz intuitiva")?
- ¿Propuesta de Valor es ÚNICA y DEFENDIBLE? Responde "por qué esto y no otra cosa".
- ¿Público Objetivo es concreto (rol + necesidad + contexto)?
- ¿Métricas de Éxito son CUANTIFICABLES?
- ¿NO hay detalles de implementación (tecnologías, frameworks, APIs)?
- ¿Lenguaje declarativo, profesional, sin ambigüedades?
- ¿No se repite lo que sí esta en el alcance en lo que no está en el alcance y viceversa?
- ¿Todo en español?

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
- Describe QUÉ cambió en este documento respecto a la versión anterior.
- Sé específico: "Se agregó la capacidad X en Capacidades Clave", "Se expandió el alcance para incluir facturación".
- Si el cambio es solo cosmético (nombre, ortografía) o no introduce nada nuevo → `redirection_summary: ""`.
- Si el cambio agrega nueva funcionalidad o entidad → escribe un resumen claro que otras fases puedan usar para decidir si necesitan actualizarse.
- Este resumen NO debe incluir sugerencias de qué hacer. Solo describe el cambio. La fase destino decidirá.

- Cada fix debe incluir ejemplo concreto.
- revision_instructions debe ser lista numerada accionable.
- Si el draft tiene 90% bien, APRUEBALO. No rechaces por P2.

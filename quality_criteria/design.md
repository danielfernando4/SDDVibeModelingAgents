# Criterios de Calidad - Diseño (BUML Python)

Evalúa el script Python del diagrama de clases contra los siguientes criterios.

## 0. Alineación con el Prompt (EVALUAR PRIMERO)
- ¿Las clases modelan el dominio que pidió el usuario?
- ¿Cada clase está justificada por un requisito o el producto?

## 1. Criterios Estructurales (Sintaxis BUML)
- **¿El script es Python VÁLIDO?** Si tiene errores de sintaxis, es P0.
- **¿Imports correctos?** Solo `from besser.BUML.metamodel.structural import (...)` con los types usados.
- **¿Todas las clases tienen `Class(name="...")`?** PascalCase, UNA palabra, sin espacios ni tildes.
- **¿Al menos 3 atributos por clase no-enum?** Cada atributo: `Property(name="...", type=...)`.
- **¿Variables de atributo con formato `Clase_atributo`?** Ej: `Paciente_nombre`, no `nombre` solo.
- **¿Enumerados bien definidos?** `Enumeration(name="...", literals={EnumerationLiteral(...)})`. Mínimo 2 literales. Nombres de literales en MAYÚSCULAS.
- **¿Asignación de atributos a clases?** `Clase.attributes = {attr1, attr2, ...}`.
- **¿Relaciones con `BinaryAssociation`?** `ends={Property(...), Property(...)}`. Cada end con name, type, multiplicity.
- **¿Multiplicidades correctas?** `Multiplicity(min, max)` o `Multiplicity(min, "*")`.
- **¿`is_composite=True` en composiciones?** Cuando la parte no existe sin el todo.
- **¿Herencia con `Generalization(general=Padre, specific=Hija)`?** Cuando hay relación "es-un".
- **¿`DomainModel` al final?** Con name, types (set de todas las clases+enums), associations (set de relaciones), generalizations (set de herencias).
- **¿NO hay variables huérfanas?** Toda Property debe estar en el `.attributes` de alguna clase.
- **¿NO hay clases huérfanas?** Toda clase debe aparecer en al menos una relación.
- **¿NO hay imports no usados?** No importar `TimeType` si no se usa.
- **¿NO hay explicaciones ni markdown?** Solo código Python puro.

## 2. Criterios Semánticos / Contenido
- ¿Clases representan entidades del dominio real? No técnicas (DatabaseManager, ApiController).
- ¿Relaciones con semántica correcta? Composición (`is_composite=True`) para "no existe sin", Herencia para "es-un".
- ¿Multiplicidades reflejan reglas de negocio? Ej: médico máximo 6 citas/día → `Multiplicity(0, 6)`.
- ¿Sin clases duplicadas o redundantes?
- ¿Nombres de variables en español, sin tildes?
- ¿Nombres de atributos descriptivos? No `temp`, `aux`, `dato1`.

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
  "redirection_summary": "<resumen de cambios para propagar, o ''>"
}

## PROPAGACIÓN DE CAMBIOS
- Describe QUÉ cambió: "Se agregó la clase Prescripcion con 3 atributos y relación con Paciente".
- Si el cambio es cosmético → `redirection_summary: ""`.
- Si el cambio agrega nuevas clases/entidades → escribe un resumen claro.
- NO incluyas críticas negativas en el summary. Solo describe el cambio.

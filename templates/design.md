# Diagrama de Clases (formato BUML Python)

El diseño debe generarse como un script Python ejecutable que define un modelo de dominio BUML.

## ESTRUCTURA DEL SCRIPT

```python
from besser.BUML.metamodel.structural import (
    Class, Property, Method, Parameter,
    BinaryAssociation, Generalization, DomainModel,
    Enumeration, EnumerationLiteral, Multiplicity,
    StringType, IntegerType, FloatType, BooleanType,
    DateType, TimeType, DateTimeType, AnyType
)

# ============================================
# ENUMERACIONES
# ============================================
NombreEnum = Enumeration(name="NombreEnum", literals={
    EnumerationLiteral(name="VALOR1"),
    EnumerationLiteral(name="VALOR2")
})

# ============================================
# CLASES (crear objetos Class primero)
# ============================================
NombreClase = Class(name="NombreClase")

# ============================================
# ATRIBUTOS (Property)
# ============================================
NombreClase_atributo = Property(name="atributo", type=StringType)
NombreClase_atributo2 = Property(name="atributo2", type=IntegerType)
NombreClase.attributes = {NombreClase_atributo, NombreClase_atributo2}

# ============================================
# MÉTODOS (opcional, solo si son relevantes al dominio)
# ============================================
NombreClase_metodo = Method(
    name="nombreMetodo",
    parameters={Parameter(name="param", type=StringType)},
    type=BooleanType
)
NombreClase.methods = {NombreClase_metodo}

# ============================================
# RELACIONES (BinaryAssociation)
# ============================================
nombre_rel = BinaryAssociation(name="nombre_rel", ends={
    Property(name="origen", type=ClaseOrigen, multiplicity=Multiplicity(1, 1)),
    Property(name="destino", type=ClaseDestino, multiplicity=Multiplicity(0, "*"), is_composite=True)
})

# ============================================
# HERENCIA (Generalization)
# ============================================
gen_nombre = Generalization(general=ClasePadre, specific=ClaseHija)

# ============================================
# DOMAIN MODEL (contenedor final)
# ============================================
domain_model = DomainModel(
    name="NombreDelSistema",
    types={Clase1, Clase2, Enum1},
    associations={rel1, rel2},
    generalizations={gen1}
)
```

## REGLAS ESTRICTAS

### Nombres de variables Python
- Clases: `PascalCase`, sin espacios, sin tildes. Ej: `Paciente`, `CitaMedica`
- Atributos: `NombreClase_nombreAtributo`. Ej: `Paciente_nombre`, `Cita_fecha`
- Métodos: `NombreClase_nombreMetodo`. Ej: `Paciente_agendarCita`
- Relaciones: `origen_destino` o nombre descriptivo. Ej: `paciente_citas`
- Enums: `PascalCase`. `EnumerationLiteral(name="MAYUSCULAS_CON_GUIONES")`

### Tipos
- `StringType`, `IntegerType`, `FloatType`, `BooleanType`, `DateType`, `TimeType`, `DateTimeType`, `AnyType`
- Para referencias a otras clases: usar el objeto Class directamente. Ej: `type=Paciente`
- Para referencias a enums: usar el objeto Enumeration. Ej: `type=EstadoCita`

### Relaciones
- `is_composite=True` → Composición (la parte no existe sin el todo)
- `is_composite=False` (default) → Asociación normal
- `Generalization(general=Padre, specific=Hija)` → Herencia
- Multiplicidades: `Multiplicity(1, 1)`, `Multiplicity(0, 1)`, `Multiplicity(0, "*")`, `Multiplicity(1, "*")`

### Mínimos
- Cada clase no-enum: mínimo 3 atributos
- Enums: mínimo 2 literales
- Cada clase debe tener al menos una relación (salvo justificación)
- Los métodos son OPCIONALES. Solo incluir si son relevantes al dominio.
- El DomainModel debe incluir TODAS las clases, enums, relaciones y generalizations.

### PROHIBIDO
- NO usar caractéres especiales en nombres (ñ, tildes, espacios)
- NO crear clases técnicas (DatabaseManager, ApiController, Router)
- NO usar `"""` (triple comilla) dentro de strings de código
- NO incluir explicaciones ni markdown. Solo el código Python puro.
- NO usar `print()` ni `import` adicionales
- NO usar `# type: ignore` ni comentarios de tipo

# Diagrama de Clases (formato Besser BUML)

El diseño debe generarse como JSON con esta estructura EXACTA:

```json
{
  "systemName": "NombreDelSistema",
  "classes": [
    {
      "className": "NombreClase",
      "attributes": [
        {"name": "nombreAtributo", "type": "String", "visibility": "public"}
      ],
      "methods": [
        {"name": "nombreMetodo", "returnType": "void", "visibility": "public", "parameters": []}
      ],
      "isAbstract": false,
      "isEnumeration": false
    }
  ],
  "relationships": [
    {
      "type": "Association",
      "source": "ClaseOrigen",
      "target": "ClaseDestino",
      "sourceMultiplicity": "1",
      "targetMultiplicity": "0..*",
      "name": "nombreRelacion"
    }
  ]
}
```

REGLAS:
- className: PascalCase, UNA palabra, sin espacios ni tildes
- atributos: mínimo 3 por clase (no-enum). camelCase, sin tildes
- tipos válidos: String, int, bool, float, boolean, Date, o nombre de clase/enum
- parámetros de métodos: array de objetos [{name, type}], NO array de strings
- enumerados (isEnumeration=true): atributos solo con "name" en MAYÚSCULAS
- relaciones: Association, Inheritance, Composition, Aggregation, Realization, Dependency
- multiplicidades: 1, 0..1, 0..*, 1..*
- NO incluir campos "position", "x", "y" (el layout es automático)
- NO duplicar relaciones
- NO usar bloques de código markdown (```json). Solo el JSON puro

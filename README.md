# Evaluador de Lenguaje Claro

Pipeline de evaluación automática de documentos administrativos españoles según criterios de **lenguaje claro**. Utiliza LangGraph con múltiples agentes Claude en paralelo para analizar 41 ítems distribuidos en 5 secciones.

## Requisitos

- Python 3.9+
- `langchain-anthropic`, `langgraph`, `pydantic`
- Variable de entorno `ANTHROPIC_API_KEY`

## Uso

```bash
# Documento de ejemplo incluido
python -m evaluador_lc.main

# Desde un archivo
python -m evaluador_lc.main documento.txt

# Desde stdin
cat documento.txt | python -m evaluador_lc.main
```

### Desde código

```python
from evaluador_lc import crear_grafo, formatear_informe

grafo = crear_grafo()
resultado = grafo.invoke({"texto": "..."})
print(formatear_informe(resultado["informe_final"]))
```

## Cómo funciona

El pipeline ejecuta 7 agentes encadenados:

| Agente | Rol |
|--------|-----|
| SA-0 Clasificador | Detecta la tipología del documento (resolución, notificación, carta…) |
| SA-1..SA-5 Evaluadores | Evalúan en paralelo los 41 ítems de las 5 secciones |
| SA-6a Calculador | Calcula puntuaciones (Python puro, sin LLM) |
| SA-6b Sintetizador | Genera el resumen narrativo con puntos fuertes y áreas de mejora |

### Secciones evaluadas

1. **Facilita la localización** — estructura, epígrafes, listados, formato (11 ítems)
2. **Mejora la comprensión: ideas** — orden sintáctico, longitud de frases, coherencia (10 ítems)
3. **Personaliza y humaniza** — voz activa, tratamiento, tono (7 ítems)
4. **Elige palabras sencillas** — tecnicismos, siglas, arcaísmos, nominalizaciones (10 ítems)
5. **Facilita la toma de decisiones** — instrucciones, plazos, procedimientos (3 ítems)

### Salida

```
======================================================================
  PUNTUACIÓN GENERAL: 72.5%
======================================================================

DESGLOSE POR SECCIÓN:
  Sección 1 – Facilita la localización: 63.6%
  ...

PUNTOS FUERTES:
  ✓ ...

ÁREAS DE MEJORA:
  ✗ ...

RESUMEN:
  ...

TABLA DETALLADA
----------------------------------------------------------------------
Sec   Ítem                                          Eval.        Comentario
```

Cada ítem se evalúa como **Sí**, **No** o **No compete** (cuando el tipo de documento no requiere ese criterio).

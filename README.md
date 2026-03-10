# Plain Language Evaluator · Evaluador de Lenguaje Claro

> A LangGraph multi-agent pipeline that scores Spanish administrative documents against 41 plain-language criteria — 5 evaluators in parallel, results in seconds.

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-multi--agent-blueviolet)](https://github.com/langchain-ai/langgraph)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-orange)](https://groq.com)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://rubendelafuente.github.io/lc-graph/)

## Live demo

**[→ Try it in your browser](https://rubendelafuente.github.io/lc-graph/)** — no installation, no server. Bring your own Groq API key.

## How it works

```
texto
  └─► SA-0  Clasificador ─────────────────────────► tipologia
                │
                ├─► SA-1  Facilita la localización ──┐
                ├─► SA-2  Mejora la comprensión    ──┤ parallel
                ├─► SA-3  Personaliza y humaniza   ──┼─► resultados_secciones
                ├─► SA-4  Elige palabras sencillas ──┤
                └─► SA-5  Toma de decisiones       ──┘
                                                   │
                                     SA-6a  Calculador ──► puntuacion
                                                              │
                                          SA-6b  Sintetizador ──► informe_final
```

**7 LLM calls total:** 1 classifier + 5 parallel evaluators + 1 synthesizer. SA-6a (scoring) is pure Python — no LLM.

Each document is evaluated against **41 criteria** across 5 sections. Each criterion is scored **Sí / No / No compete** (not applicable items are excluded from the score denominator).

## Sample output

```
======================================================================
  PUNTUACIÓN GENERAL: 52.3%
======================================================================

DESGLOSE POR SECCIÓN:
  Sección 1 – Facilita la localización:       63.6%
  Sección 2 – Mejora la comprensión (ideas):  50.0%
  Sección 3 – Personaliza y humaniza:         42.9%
  Sección 4 – Elige palabras sencillas:       40.0%
  Sección 5 – Facilita la toma de decisiones: 66.7%

PUNTOS FUERTES:
  ✓ El documento incluye epígrafes numerados que facilitan la navegación.
  ✓ Las instrucciones para el ciudadano están ordenadas paso a paso.

ÁREAS DE MEJORA:
  ✗ Las frases superan con frecuencia las 30 palabras recomendadas.
  ✗ Abundan las nominalizaciones y el léxico administrativo arcaico.

RESUMEN:
  La resolución muestra una estructura clara con epígrafes bien definidos,
  pero el lenguaje resulta denso y distante. Simplificar frases y sustituir
  términos jurídicos por alternativas cotidianas mejoraría notablemente la
  comprensión ciudadana.

TABLA DETALLADA
----------------------------------------------------------------------
Sec   Ítem                                          Eval.        Comentario
 1    El documento tiene título claro y visible     Sí           Título en mayúsculas, visible
 1    Usa epígrafes o títulos intermedios           Sí           PRIMERO, SEGUNDO, TERCERO
 1    Las referencias legales no interrumpen...     No           Cita legislativa extensa en el cuerpo
...
```

## Quickstart

```bash
pip install langchain-groq langgraph pydantic
export GROQ_API_KEY=gsk_...

# Run with the built-in example document
python -m evaluador_lc.main

# Evaluate a file
python -m evaluador_lc.main documento.txt

# Evaluate via stdin
cat documento.txt | python -m evaluador_lc.main
```

## Python API

```python
from evaluador_lc import crear_grafo, formatear_informe

grafo = crear_grafo()
resultado = grafo.invoke({"texto": "..."})
print(formatear_informe(resultado["informe_final"]))
```

## Secciones evaluadas

| # | Sección | Ítems |
|---|---------|-------|
| 1 | Facilita la localización — estructura, epígrafes, listados, formato | 11 |
| 2 | Mejora la comprensión: ideas — orden sintáctico, longitud, coherencia | 10 |
| 3 | Personaliza y humaniza — voz activa, tratamiento, tono | 7 |
| 4 | Elige palabras sencillas — tecnicismos, siglas, arcaísmos, nominalizaciones | 10 |
| 5 | Facilita la toma de decisiones — instrucciones, plazos, procedimientos | 3 |
| | **Total** | **41** |

## Tech stack

[LangGraph](https://github.com/langchain-ai/langgraph) · [LangChain Groq](https://python.langchain.com/docs/integrations/chat/groq/) · [Pydantic](https://docs.pydantic.dev/) · [Llama 3.3 70b via Groq](https://groq.com)

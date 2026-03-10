# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Pipeline

```bash
# Run with the built-in example document
python -m evaluador_lc.main

# Evaluate a text file
python -m evaluador_lc.main documento.txt

# Evaluate via stdin
cat documento.txt | python -m evaluador_lc.main
```

Requires `GROQ_API_KEY` set in the environment. The package is imported as `evaluador_lc` (the directory is `lc-graph` but the module lives under `evaluador_lc`).

## Architecture

This is a **LangGraph multi-agent pipeline** for evaluating Spanish administrative documents against "plain language" (lenguaje claro) criteria. The pipeline uses `llama-3.3-70b-versatile` via Groq exclusively.

### Graph flow (`pipeline.py`)

```
SA-0 clasificador
      │ (fan-out)
      ├── SA-1 evaluador_s1
      ├── SA-2 evaluador_s2   } parallel
      ├── SA-3 evaluador_s3   }
      ├── SA-4 evaluador_s4   }
      └── SA-5 evaluador_s5
      │ (fan-in)
SA-6a calculador   ← pure Python, no LLM
      │
SA-6b sintetizador ← LLM
      │
     END
```

- **SA-0** classifies the document type (`TipologiaDocumental` enum: resolución, notificación, carta, etc.)
- **SA-1 through SA-5** evaluate 41 total items across 5 sections in parallel; results accumulate via a custom reducer (`_merge_resultados`) into `EstadoPipeline.resultados_secciones`
- **SA-6a** computes scores from Python logic (no LLM call)
- **SA-6b** generates the narrative summary from the aggregated scores

### Key data models (`models.py`)

- `ItemEvaluado` — single criterion result: `evaluacion` ∈ {Sí, No, No compete}
- `ResultadoSeccion` — all items for one section
- `ResultadoClasificacion` — SA-0 output
- `PuntuacionGlobal` / `PuntuacionSeccion` — computed scores
- `InformeFinal` — top-level output: scores + puntos_fuertes + areas_mejora + resumen_narrativo + tabla_detallada

### Prompts (`prompts.py`)

Each section agent (SA-1..SA-5) uses a dedicated prompt constant (`PROMPT_SECCION_1`..`5`). All prompts instruct the LLM to respond with raw JSON (no markdown fences). The helper `_limpiar_json` strips accidental fences before `json.loads`.

### Public API (`__init__.py`)

```python
from evaluador_lc import crear_grafo, formatear_informe, InformeFinal
grafo = crear_grafo()
resultado = grafo.invoke({"texto": "..."})
print(formatear_informe(resultado["informe_final"]))
```

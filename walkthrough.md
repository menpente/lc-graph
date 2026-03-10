# Pipeline Walkthrough — lc-graph

End-to-end explanation of the Python LangGraph pipeline.

---

## Entry point — `main.py`

```
python -m evaluador_lc.main [archivo.txt]
```

Reads text from a file, stdin, or falls back to a hardcoded `DOCUMENTO_EJEMPLO` (a Spanish administrative resolution). Then:

```python
grafo = crear_grafo()
resultado = grafo.invoke({"texto": "..."})
print(formatear_informe(resultado["informe_final"]))
```

Three lines. The entire pipeline is inside `grafo.invoke()`.

---

## State — `pipeline.py` `EstadoPipeline`

A LangGraph `TypedDict` that all nodes read from and write to:

```
texto                   → input (never mutated)
tipologia               → set by SA-0
justificacion_tipologia → set by SA-0
resultados_secciones    → accumulated by SA-1..5 via _merge_resultados reducer
puntuacion              → set by SA-6a
informe_final           → set by SA-6b
```

The `resultados_secciones` field uses a custom **reducer** (`_merge_resultados = existing + new`) so that when 5 parallel branches each return `[ResultadoSeccion]`, LangGraph merges them into one list instead of overwriting.

---

## SA-0 — Clasificador

**Prompt:** sends the raw document text, asks the LLM to pick one of 11 document types (`resolución`, `notificación`, `carta`, etc.).

**Output JSON:**
```json
{ "tipologia": "resolución", "justificacion": "..." }
```

Parsed into `ResultadoClasificacion` (Pydantic). Writes `tipologia` and `justificacion_tipologia` into state.

Model: `claude-sonnet-4-20250514`, temp=0, max_tokens=**500** (small, classification only).

---

## SA-1..5 — Evaluadores (parallel)

Created by the factory `_crear_nodo_evaluador(seccion)`. All 5 nodes run **in parallel** in LangGraph (via fan-out edges from `clasificador` to each `evaluador_s{n}`).

Each one:
1. Formats the section-specific prompt with `{texto}` and `{tipologia}`
2. Calls the LLM → gets JSON with `seccion`, `nombre_seccion`, and `items[]`
3. Each item has: `seccion`, `item` (description), `evaluacion` (`Sí`/`No`/`No compete`), `comentario`
4. Returns `{"resultados_secciones": [ResultadoSeccion(...)]}`

The reducer merges all 5 into one list.

**Section breakdown:**
| SA | Section | Items |
|----|---------|-------|
| 1 | Facilita la localización | 11 |
| 2 | Mejora la comprensión (ideas) | 10 |
| 3 | Personaliza y humaniza | 7 |
| 4 | Elige palabras sencillas | 10 |
| 5 | Facilita la toma de decisiones | 3 |
| | **Total** | **41** |

Model: temp=0, max_tokens=**4096** (longer structured JSON output).

---

## SA-6a — Calculador (pure Python, no LLM)

Iterates over `resultados_secciones` for sections 1–5. For each:

```python
total_si   = count items where evaluacion == "Sí"
total_no   = count items where evaluacion == "No"
evaluables = total_si + total_no   # "No compete" excluded from denominator
porcentaje = round((total_si / evaluables) * 100, 1)
```

Then aggregates across all sections for a global `puntuacion_general`. Produces a `PuntuacionGlobal` with a `PuntuacionSeccion` per section.

Key insight: **"No compete" items don't count against the score** — they're excluded from `evaluables`.

---

## SA-6b — Sintetizador

Takes the computed scores and gathers all items where `evaluacion == "No"`, then calls the LLM with:

```
PUNTUACIONES:
  Puntuación general: 52.3%
  Sección 1 – Facilita la localización: 63.6%
  ...

TABLA DETALLADA (ítems con "No"):
  [S1] Las referencias legales...: El documento mezcla referencias...
  [S2] Las frases son cortas...: Varias frases superan 40 palabras...
```

**Output JSON:**
```json
{
  "puntos_fuertes": ["...", "..."],
  "areas_mejora": ["...", "..."],
  "resumen_narrativo": "El documento..."
}
```

Then assembles the final `InformeFinal` object, which also includes `tabla_detallada` (all 41 items sorted by section).

Model: temp=**0.3** (slightly creative for narrative), max_tokens=2048.

---

## Output — `formatear_informe()`

Plain-text formatter. Prints:
1. Global score banner
2. Per-section breakdown
3. Puntos fuertes / Áreas de mejora lists
4. Resumen narrativo
5. Full 41-row table: `Sec | Ítem | Eval. | Comentario`

---

## Data flow summary

```
texto
  └─► SA-0 clasificador ──────────────────────────► tipologia
                │
                ├─► SA-1 evaluador_s1 ──┐
                ├─► SA-2 evaluador_s2 ──┤
                ├─► SA-3 evaluador_s3 ──┼─► resultados_secciones (merged)
                ├─► SA-4 evaluador_s4 ──┤
                └─► SA-5 evaluador_s5 ──┘
                                        │
                              SA-6a calculador ──► puntuacion
                                                       │
                                           SA-6b sintetizador ──► informe_final
```

**7 LLM calls total** — 1 classifier + 5 parallel evaluators + 1 synthesizer. SA-6a is pure Python.

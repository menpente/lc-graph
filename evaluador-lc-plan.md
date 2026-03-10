# Plan: evaluador-lc.html (single-file HTML port)

## Context

The current Python pipeline (lc-graph) runs 7 Claude API calls via LangGraph and outputs a plain-text report. The goal is to port it to a single self-contained `.html` file — same pattern as https://github.com/menpente/aclarador-html — so users can open it directly in a browser with no installation, no server, and no build step. The user provides their Anthropic API key (stored in localStorage). Everything runs client-side.

## Output file

`/Users/rubendelafuente/lc-graph/evaluador-lc.html`

## Critical source files

- `prompts.py` — 7 prompts to port verbatim (convert `{{`/`}}` Python escapes → literal `{`/`}` in JS template literals)
- `pipeline.py` — `_limpiar_json`, `_llamar_llm`, `nodo_calculador` arithmetic, `nodo_sintetizador` `items_no` logic
- `models.py` — JSON field names the LLM returns (`tipologia`, `justificacion`, `seccion`, `nombre_seccion`, `items`, `evaluacion`, `comentario`, `puntos_fuertes`, `areas_mejora`, `resumen_narrativo`)

## File structure (single `<script>` block at end of `<body>`)

```
<head>: meta, Inter font, Mammoth.js CDN, PDF.js CDN, <style>
<body>:
  #app-header
  #config-panel   — API key input + show/hide button
  #input-panel    — textarea + file upload (.txt/.docx/.pdf) + "Evaluar" button
  #progress-panel — 8-step list (SA-0..SA-6b) with idle/running/done/error icons
  #error-panel    — alert div (hidden by default)
  #report-panel   — populated by renderizarInforme()
<script>:
  A. Prompt constants (template literal functions)
  B. API layer: limpiarJson(), llamarClaude()
  C. Pipeline nodes: nodoClasificador(), crearNodoEvaluador(), nodoCalculador(), nodoSintetizador()
  D. Orchestrator: ejecutarPipeline() with Promise.all() for SA-1..5
  E. File reader: leerArchivo() for .txt/.docx/.pdf
  F. Report renderer: renderizarInforme()
  G. UI handlers: DOMContentLoaded, API key persistence, file input, "Evaluar" button
```

## Key implementation details

### Anthropic browser API call
```javascript
fetch('https://api.anthropic.com/v1/messages', {
  method: 'POST',
  headers: {
    'x-api-key': apiKey,
    'anthropic-version': '2023-06-01',
    'anthropic-dangerous-direct-browser-access': 'true',  // required for CORS
    'content-type': 'application/json',
  },
  body: JSON.stringify({ model, max_tokens, temperature, messages: [{role:'user', content: prompt}] })
})
// Response: data.content[0].text  (NOT data.choices[0].message.content like OpenAI/Groq)
```

### Fan-out/fan-in (replaces LangGraph)
```javascript
// SA-1..5 run in parallel, all push to estado.resultadosSecciones[]
await Promise.all([1,2,3,4,5].map(n => crearNodoEvaluador(n)(estado, apiKey)));
// Safe: JS is single-threaded, array.push() calls don't interleave
```

### Prompt porting rule
Python `{{` and `}}` (escapes for `.format()`) → plain `{` and `}` in JS template literals
Python `{texto}` → `${texto}` in JS template literals

### Models used (same as Python)
- SA-0, SA-1..5: `claude-sonnet-4-20250514`, temp=0, max_tokens=500/4096
- SA-6b: `claude-sonnet-4-20250514`, temp=0.3, max_tokens=2048
- SA-6a (calculador): pure JS, no API call

### Score calculation (port of nodo_calculador)
```javascript
const porcentaje = evaluables > 0 ? Math.round((totalSi / evaluables) * 1000) / 10 : null;
```

### CDN dependencies
- Mammoth (docx): `https://cdn.jsdelivr.net/npm/mammoth@1.6.0/mammoth.browser.min.js`
- PDF.js: `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js`
- PDF.js worker: `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js`
- Google Fonts (Open Sans): `https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;500;600;700&display=swap`

## Visual design — Cálamo & Cran aesthetic

Reference: https://www.calamoycran.com/cursos/procesamiento-del-lenguaje-natural/

### Color palette
| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary` | `#2ea3f2` | Links, buttons, accents, step icons, progress |
| `--color-text` | `#333333` | Headings |
| `--color-text-body` | `#666666` | Body text, labels, muted content |
| `--color-text-muted` | `#999999` | Secondary/placeholder text |
| `--color-border` | `#e2e2e2` | Panel borders, table dividers, inputs |
| `--color-border-light` | `#eeeeee` | Subtle row separators |
| `--color-bg` | `#ffffff` | Page background |
| `--color-bg-section` | `#f9f9f9` | Alternating section backgrounds |
| `--color-error` | `#e74c3c` | Errors |
| `--color-success` | `#27ae60` | Sí evaluations, puntos fuertes |
| `--color-warning` | `#e67e22` | Áreas de mejora |

### Typography
- **Font family**: `'Open Sans', Arial, sans-serif` (not Inter)
- **Font weight**: `500` throughout (Open Sans medium) — heavier than typical body weight
- **Line height**: `1.7em` for body text
- **Sizes**: H1 30px · H2 26px · H3 22px · H4 18px · body 14px
- All headings at weight 500 (not bold 700), color `#333`
- Links: `#2ea3f2`, no underline

### Layout
- Max-width container: **1080px**, centered, `80%` width on desktop
- Clean white background, no dark sections or gradients
- Consistent section padding; generous whitespace between elements
- Paragraph margin-bottom: `30px`

### UI components

**Buttons**
- Font size: `16px`, weight `500`
- Border: `2px solid #2ea3f2`
- Border-radius: `3px` (very slight — nearly square)
- Primary: `background #2ea3f2`, white text
- Hover: slight `rgba(0,0,0,0.05)` overlay
- Transition: `0.2s`

**Inputs / textarea**
- Border: `1px solid #e2e2e2`
- Border-radius: `3px`
- Font: `14px Open Sans`
- Focus: border-color `#2ea3f2`, no box-shadow

**Panels / cards**
- White background, `1px solid #e2e2e2` border
- Border-radius: `3px`
- Minimal shadow (or none) — flat aesthetic
- Section titles in `#333`, `500` weight, `18px`

**Table**
- Clean, no outer border
- `1px solid #eeeeee` row separators
- Header row: `background #f9f9f9`, text `#999`, `12px`, uppercase, letter-spacing
- Cell padding: `10px 12px`
- Hover row: `background #f9f9f9`

**Score badge**
- Circle, background `#2ea3f2` (primary blue) unless score-coded:
  - < 41% → `#e74c3c` (red)
  - 41–70% → `#e67e22` (orange, not amber)
  - 71–90% → `#27ae60` (green)
  - 91%+ → `#1a8a4a` (dark green)
- White text, weight `700`

**Progress steps**
- Running: left border `3px solid #2ea3f2`, background `#f0f8fe`
- Done: left border `3px solid #27ae60`, background `#f0faf4`
- Error: left border `3px solid #e74c3c`, background `#fdf4f4`
- Idle: no background, text `#999`
- Spinner: CSS `border` animation in `#2ea3f2` (no Unicode glyphs)

**Eval badges (table)**
- `Sí`: background `#eafaf1`, color `#27ae60`, border `1px solid #a9dfbf`
- `No`: background `#fdf0ef`, color `#e74c3c`, border `1px solid #f5b7b1`
- `No compete`: background `#f4f4f4`, color `#999`, border `1px solid #ddd`
- All: `border-radius 3px`, `font-size 12px`, `padding 2px 8px`

### Tone
Clean, professional, educational. No gradients, no shadows (or very subtle). The `#2ea3f2` blue is the only accent color — everything else is grays and whites.

## Report rendering

Replace Python's plain-text `formatear_informe()` with styled HTML:
- Big score badge (color-coded: <41% red, 41-70% amber, 71-90% green, 91%+ dark green)
- CSS Grid cards for each of 5 sections (name, bar, Sí/No/NC counts)
- Two-column puntos fuertes / áreas de mejora lists
- Resumen narrativo paragraph
- Full 41-item `<table>` with colored Evaluación cells (`eval-si`, `eval-no`, `eval-nc`)

## Error handling
- `llamarClaude()` throws enriched Error on HTTP failure or JSON parse failure
- Evaluator node errors mark the step icon as error and re-throw (fails fast via Promise.all)
- UI handler catches all errors and shows in `#error-panel`
- File reading errors shown separately, don't disable "Evaluar"

## Progress steps (8 total)
| Index | Label | Sub |
|-------|-------|-----|
| 0 | SA-0 · Clasificador | Identifica la tipología documental |
| 1 | SA-1 · Facilita la localización | 11 ítems |
| 2 | SA-2 · Mejora la comprensión (ideas) | 10 ítems |
| 3 | SA-3 · Personaliza y humaniza | 7 ítems |
| 4 | SA-4 · Palabras sencillas | 10 ítems |
| 5 | SA-5 · Toma de decisiones | 3 ítems |
| 6 | SA-6a · Calculador | Cálculo de puntuaciones (sin LLM) |
| 7 | SA-6b · Sintetizador | Resumen narrativo |

## Verification
1. Open `evaluador-lc.html` in Chrome/Edge — no server needed
2. Enter a valid `ANTHROPIC_API_KEY`
3. Paste the sample document from `main.py` (DOCUMENTO_EJEMPLO)
4. Click "Evaluar" — verify all 8 steps complete and the report renders
5. Check overall score and per-section breakdown match a reference Python run
6. Test .txt file upload
7. Reload page — verify API key is restored from localStorage

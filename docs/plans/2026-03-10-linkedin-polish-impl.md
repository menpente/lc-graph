# LinkedIn Portfolio Polish — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the lc-graph repo into a polished LinkedIn portfolio piece with clean structure, English-primary README, and a live GitHub Pages demo.

**Architecture:** Move Python source files into a proper `evaluador_lc/` package, reorganize docs, add packaging metadata, and overhaul the README. No code logic changes — pure structure and documentation.

**Tech Stack:** Python 3.9+, LangGraph, LangChain Anthropic, Pydantic, plain HTML/JS (existing)

---

### Task 1: Create `evaluador_lc/` package directory

The Python source files (`__init__.py`, `main.py`, `pipeline.py`, `models.py`, `prompts.py`) currently live at the repo root. They need to move into `evaluador_lc/` so `python -m evaluador_lc.main` works correctly when the repo root is in `PYTHONPATH`.

**Files:**
- Create: `evaluador_lc/__init__.py` (move from root `__init__.py`)
- Create: `evaluador_lc/main.py` (move from root `main.py`)
- Create: `evaluador_lc/pipeline.py` (move from root `pipeline.py`)
- Create: `evaluador_lc/models.py` (move from root `models.py`)
- Create: `evaluador_lc/prompts.py` (move from root `prompts.py`)
- Delete: root-level `__init__.py`, `main.py`, `pipeline.py`, `models.py`, `prompts.py`

**Step 1: Move files**

```bash
mkdir -p evaluador_lc
git mv __init__.py evaluador_lc/__init__.py
git mv main.py evaluador_lc/main.py
git mv pipeline.py evaluador_lc/pipeline.py
git mv models.py evaluador_lc/models.py
git mv prompts.py evaluador_lc/prompts.py
```

**Step 2: Verify the package can be imported**

```bash
python -c "from evaluador_lc import crear_grafo, formatear_informe, InformeFinal; print('OK')"
```

Expected output: `OK`

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: move source into evaluador_lc/ package"
```

---

### Task 2: Reorganize docs and delete internal files

**Files:**
- Move: `walkthrough.md` → `docs/walkthrough.md`
- Move: `evaluador-lc.html` → `docs/index.html`
- Delete: `evaluador-lc-plan.md` (internal planning doc, not portfolio material)
- `docs/plans/` already exists from design doc commit

**Step 1: Move and delete**

```bash
git mv walkthrough.md docs/walkthrough.md
git mv evaluador-lc.html docs/index.html
git rm evaluador-lc-plan.md
```

**Step 2: Verify docs structure**

```bash
ls docs/
```

Expected: `index.html  plans/  walkthrough.md`

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: reorganize docs, move HTML demo to docs/index.html"
```

---

### Task 3: Add `.gitignore`

**Files:**
- Create: `.gitignore`

**Step 1: Write `.gitignore`**

```
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/
.eggs/

# Environments
.env
.venv
venv/
env/

# IDE / OS
.DS_Store
.idea/
.vscode/
*.swp

# Test / coverage
.pytest_cache/
.coverage
htmlcov/
```

**Step 2: Verify `.DS_Store` is ignored**

```bash
git status
```

Expected: `.DS_Store` no longer appears as untracked.

**Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: add .gitignore"
```

---

### Task 4: Add `pyproject.toml`

**Files:**
- Create: `pyproject.toml`

**Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "evaluador-lc"
version = "0.1.0"
description = "LangGraph multi-agent pipeline for plain-language evaluation of Spanish administrative documents"
requires-python = ">=3.9"
dependencies = [
    "langchain-anthropic",
    "langgraph",
    "pydantic",
]

[project.urls]
Homepage = "https://github.com/rubendelafuente/lc-graph"
"Live Demo" = "https://rubendelafuente.github.io/lc-graph/"
```

**Step 2: Verify it parses**

```bash
python -c "import tomllib; tomllib.loads(open('pyproject.toml').read()); print('OK')"
```

Expected: `OK` (Python 3.11+) — if on 3.9/3.10, skip this step.

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add pyproject.toml with package metadata"
```

---

### Task 5: Add MIT `LICENSE`

**Files:**
- Create: `LICENSE`

**Step 1: Write `LICENSE`**

```
MIT License

Copyright (c) 2026 Rubén de la Fuente

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Step 2: Commit**

```bash
git add LICENSE
git commit -m "chore: add MIT license"
```

---

### Task 6: Rewrite `README.md`

This is the most important task for LinkedIn. English primary, scannable, both audiences served.

**Files:**
- Modify: `README.md`

**Step 1: Replace README content**

```markdown
# Plain Language Evaluator · Evaluador de Lenguaje Claro

> A LangGraph multi-agent pipeline that scores Spanish administrative documents against 41 plain-language criteria — 5 evaluators in parallel, results in seconds.

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-multi--agent-blueviolet)](https://github.com/langchain-ai/langgraph)
[![Claude](https://img.shields.io/badge/Claude-Sonnet-orange)](https://www.anthropic.com)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://rubendelafuente.github.io/lc-graph/)

## Live demo

**[→ Try it in your browser](https://rubendelafuente.github.io/lc-graph/)** — no installation, no server. Bring your own Anthropic API key.

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
pip install langchain-anthropic langgraph pydantic
export ANTHROPIC_API_KEY=sk-ant-...

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

[LangGraph](https://github.com/langchain-ai/langgraph) · [LangChain Anthropic](https://python.langchain.com/docs/integrations/chat/anthropic/) · [Pydantic](https://docs.pydantic.dev/) · [Claude Sonnet](https://www.anthropic.com/claude)
```

**Step 2: Verify README renders correctly**

Open `README.md` in a Markdown previewer (VS Code or GitHub web UI) and check:
- Badges show on the first line
- ASCII diagram is inside a fenced code block (no mangling)
- Sample output block is readable
- Tables align

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README in English with live demo, sample output, badges"
```

---

### Task 7: Final verification

**Step 1: Check repo structure**

```bash
ls -la
```

Expected files at root: `README.md`, `LICENSE`, `pyproject.toml`, `.gitignore`, `evaluador_lc/`, `docs/`, `CLAUDE.md`

Expected NOT at root: `__init__.py`, `main.py`, `pipeline.py`, `models.py`, `prompts.py`, `evaluador-lc.html`, `evaluador-lc-plan.md`, `walkthrough.md`

**Step 2: Verify Python import works**

```bash
python -c "from evaluador_lc import crear_grafo, formatear_informe, InformeFinal; print('Import OK')"
```

Expected: `Import OK`

**Step 3: Check git log**

```bash
git log --oneline -8
```

Expected: clean commit history showing each polish step.

**Step 4: Enable GitHub Pages**

In the GitHub repo settings → Pages → Source: "Deploy from branch" → Branch: `main` → Folder: `/docs`. The live demo will be available at `https://rubendelafuente.github.io/lc-graph/`.

(This is a manual step in the GitHub UI — cannot be done via git.)

---

### Task 8: Push to GitHub

```bash
git push origin main
```

Then verify the README renders correctly on the GitHub repo page.

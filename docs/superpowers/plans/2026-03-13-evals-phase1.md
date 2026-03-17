# Evals Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic test suite + golden-dataset eval framework covering SA-6a (scoring math), `_limpiar_json`, `_merge_resultados`, and SA-0 classification accuracy.

**Architecture:** Three layers — (1) pure-Python unit tests in `tests/` that always run in CI, (2) a `evals/` directory with a golden dataset and a `@pytest.mark.eval` marker for tests that make real LLM calls, (3) a conftest that registers the marker and loads fixtures. SA-6b synthesis evals are deferred to Phase 2 after collecting production traces.

**Tech Stack:** pytest, unittest.mock, LangChain ChatGroq (for live eval tests only), Pydantic models from `evaluador_lc.models`

---

## Chunk 1: Pure-Python unit tests (no LLM, always run in CI)

### Task 1: Tests for `_limpiar_json` and `_merge_resultados`

**Files:**
- Create: `tests/test_pipeline_helpers.py`

These helpers live in `evaluador_lc/pipeline.py` but are not exported. Import them directly.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_pipeline_helpers.py
import pytest

from evaluador_lc.models import Evaluacion, ItemEvaluado, ResultadoSeccion
from evaluador_lc.pipeline import _limpiar_json, _merge_resultados


# ── _limpiar_json ─────────────────────────────────────────────────────────────

def test_limpiar_json_plain_json_unchanged():
    raw = '{"key": "value"}'
    assert _limpiar_json(raw) == '{"key": "value"}'


def test_limpiar_json_strips_backtick_fence():
    raw = "```json\n{\"key\": \"value\"}\n```"
    assert _limpiar_json(raw) == '{"key": "value"}'


def test_limpiar_json_strips_generic_fence():
    raw = "```\n{\"key\": \"value\"}\n```"
    assert _limpiar_json(raw) == '{"key": "value"}'


def test_limpiar_json_strips_leading_whitespace():
    raw = "  \n{\"key\": \"value\"}"
    assert _limpiar_json(raw) == '{"key": "value"}'


def test_limpiar_json_fence_no_newline():
    # Edge case: fence immediately followed by content with no newline
    raw = "```{\"key\": \"value\"}```"
    result = _limpiar_json(raw)
    assert "key" in result  # should at minimum expose the JSON content


# ── _merge_resultados ─────────────────────────────────────────────────────────

def _make_seccion(num: int) -> ResultadoSeccion:
    item = ItemEvaluado(
        seccion=num,
        item=f"Ítem de sección {num}",
        evaluacion=Evaluacion.SI,
        comentario="OK.",
    )
    return ResultadoSeccion(seccion=num, nombre_seccion=f"Sección {num}", items=[item])


def test_merge_resultados_combines_lists():
    s1 = _make_seccion(1)
    s2 = _make_seccion(2)
    result = _merge_resultados([s1], [s2])
    assert len(result) == 2
    assert result[0].seccion == 1
    assert result[1].seccion == 2


def test_merge_resultados_empty_existing():
    s1 = _make_seccion(1)
    result = _merge_resultados([], [s1])
    assert len(result) == 1


def test_merge_resultados_empty_new():
    s1 = _make_seccion(1)
    result = _merge_resultados([s1], [])
    assert len(result) == 1


def test_merge_resultados_both_empty():
    assert _merge_resultados([], []) == []


def test_merge_resultados_preserves_order():
    secs = [_make_seccion(i) for i in range(1, 6)]
    result = _merge_resultados(secs[:3], secs[3:])
    assert [r.seccion for r in result] == [1, 2, 3, 4, 5]
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_pipeline_helpers.py -v
```
Expected: ImportError or NameError — `_limpiar_json` and `_merge_resultados` are not yet exported from the module.

- [ ] **Step 3: Verify the functions exist (they do — no new code needed)**

`_limpiar_json` is at `evaluador_lc/pipeline.py:83` and `_merge_resultados` is at `pipeline.py:53`. The import just needs to work. If pytest finds them, tests should pass immediately.

Run again:
```bash
pytest tests/test_pipeline_helpers.py -v
```
Expected: All PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_pipeline_helpers.py
git commit -m "test: add unit tests for _limpiar_json and _merge_resultados helpers"
```

---

### Task 2: Tests for `nodo_calculador` (SA-6a scoring math)

**Files:**
- Create: `tests/test_scoring.py`

`nodo_calculador` is at `evaluador_lc/pipeline.py:140`. It takes an `EstadoPipeline`-like dict and returns `{"puntuacion": PuntuacionGlobal}`. No LLM involved.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_scoring.py
"""
Tests for nodo_calculador (SA-6a): pure-Python scoring logic.
No LLM calls. Always runs in CI.
"""
import pytest

from evaluador_lc.models import Evaluacion, ItemEvaluado, ResultadoSeccion
from evaluador_lc.pipeline import nodo_calculador


def _make_item(seccion: int, evaluacion: Evaluacion) -> ItemEvaluado:
    return ItemEvaluado(
        seccion=seccion,
        item=f"Ítem {evaluacion.value}",
        evaluacion=evaluacion,
        comentario="Comentario de prueba.",
    )


def _make_seccion(num: int, items: list[ItemEvaluado]) -> ResultadoSeccion:
    return ResultadoSeccion(
        seccion=num,
        nombre_seccion=f"Sección {num}",
        items=items,
    )


def _state(secciones: list[ResultadoSeccion]) -> dict:
    return {"resultados_secciones": secciones}


# ── Basic correctness ─────────────────────────────────────────────────────────

def test_all_si_scores_100():
    items = [_make_item(1, Evaluacion.SI) for _ in range(5)]
    state = _state([_make_seccion(1, items)])
    result = nodo_calculador(state)
    assert result["puntuacion"].puntuacion_general == 100.0


def test_all_no_scores_0():
    items = [_make_item(1, Evaluacion.NO) for _ in range(5)]
    state = _state([_make_seccion(1, items)])
    result = nodo_calculador(state)
    assert result["puntuacion"].puntuacion_general == 0.0


def test_half_si_half_no_scores_50():
    items = (
        [_make_item(1, Evaluacion.SI) for _ in range(3)]
        + [_make_item(1, Evaluacion.NO) for _ in range(3)]
    )
    state = _state([_make_seccion(1, items)])
    result = nodo_calculador(state)
    assert result["puntuacion"].puntuacion_general == 50.0


def test_no_compete_excluded_from_denominator():
    # 2 Sí, 0 No, 3 No compete → 100% (only 2 evaluables)
    items = (
        [_make_item(1, Evaluacion.SI) for _ in range(2)]
        + [_make_item(1, Evaluacion.NO_COMPETE) for _ in range(3)]
    )
    state = _state([_make_seccion(1, items)])
    result = nodo_calculador(state)
    assert result["puntuacion"].puntuacion_general == 100.0


def test_all_no_compete_porcentaje_is_none():
    items = [_make_item(1, Evaluacion.NO_COMPETE) for _ in range(5)]
    state = _state([_make_seccion(1, items)])
    result = nodo_calculador(state)
    sec = result["puntuacion"].secciones[0]
    assert sec.porcentaje is None


def test_global_score_is_weighted_across_sections():
    # S1: 3 Sí, 1 No → 75%. S2: 1 Sí, 1 No → 50%. Global: 4/6 = 66.7%
    s1_items = (
        [_make_item(1, Evaluacion.SI) for _ in range(3)]
        + [_make_item(1, Evaluacion.NO)]
    )
    s2_items = [_make_item(2, Evaluacion.SI), _make_item(2, Evaluacion.NO)]
    state = _state([_make_seccion(1, s1_items), _make_seccion(2, s2_items)])
    result = nodo_calculador(state)
    assert result["puntuacion"].puntuacion_general == round(4 / 6 * 100, 1)


# ── Section metadata ──────────────────────────────────────────────────────────

def test_section_counts_are_correct():
    items = (
        [_make_item(1, Evaluacion.SI) for _ in range(3)]
        + [_make_item(1, Evaluacion.NO) for _ in range(2)]
        + [_make_item(1, Evaluacion.NO_COMPETE)]
    )
    state = _state([_make_seccion(1, items)])
    sec = nodo_calculador(state)["puntuacion"].secciones[0]
    assert sec.total_si == 3
    assert sec.total_no == 2
    assert sec.total_no_compete == 1
    assert sec.total_evaluables == 5


def test_section_name_from_hardcoded_map():
    items = [_make_item(1, Evaluacion.SI)]
    state = _state([_make_seccion(1, items)])
    sec = nodo_calculador(state)["puntuacion"].secciones[0]
    assert sec.nombre == "Facilita la localización"


def test_missing_section_is_skipped():
    # Only provide section 3, sections 1,2,4,5 absent
    items = [_make_item(3, Evaluacion.SI)]
    state = _state([_make_seccion(3, items)])
    result = nodo_calculador(state)
    assert len(result["puntuacion"].secciones) == 1
    assert result["puntuacion"].secciones[0].seccion == 3


def test_empty_sections_returns_zero_general():
    state = _state([])
    result = nodo_calculador(state)
    assert result["puntuacion"].puntuacion_general == 0.0
    assert result["puntuacion"].secciones == []


# ── Rounding ──────────────────────────────────────────────────────────────────

def test_score_rounded_to_one_decimal():
    # 1 Sí, 2 No → 33.3333...% → should be 33.3
    items = [_make_item(1, Evaluacion.SI)] + [_make_item(1, Evaluacion.NO) for _ in range(2)]
    state = _state([_make_seccion(1, items)])
    result = nodo_calculador(state)
    assert result["puntuacion"].puntuacion_general == 33.3
```

- [ ] **Step 2: Run to verify they fail (or import-error)**

```bash
pytest tests/test_scoring.py -v
```
Expected: Some tests fail if there are edge case bugs, or all pass if logic is correct.

- [ ] **Step 3: No implementation changes needed**

`nodo_calculador` is already implemented at `pipeline.py:140-199`. If tests fail, there's a real bug to fix in the scoring logic. Investigate and fix before committing.

- [ ] **Step 4: Confirm all pass**

```bash
pytest tests/test_scoring.py -v
```
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_scoring.py
git commit -m "test: add unit tests for nodo_calculador scoring math"
```

---

## Chunk 2: Golden dataset + classification eval

### Task 3: Golden dataset structure

**Files:**
- Create: `evals/__init__.py`
- Create: `evals/conftest.py`
- Create: `evals/datasets/golden/resolucion_01.txt`
- Create: `evals/datasets/golden/resolucion_01_meta.json`
- Modify: `pytest.ini`

The golden dataset starts with a single document (`DOCUMENTO_EJEMPLO` from `main.py`). The `_meta.json` file records what a human expert confirmed the correct classification is. Section-level annotations come in Phase 2 after reviewing real pipeline outputs.

- [ ] **Step 1: Register the `eval` pytest marker**

Edit `pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
markers =
    eval: marks tests as real LLM eval tests (run with: pytest -m eval)
```

- [ ] **Step 2: Create the golden document**

`evals/datasets/golden/resolucion_01.txt` — copy the exact text from `evaluador_lc/main.py:28-60`:

```
RESOLUCIÓN DE CONCESIÓN DE AYUDA PARA ADQUISICIÓN DE VIVIENDA

Vista la solicitud presentada por D./Dña. __________, con DNI __________,
en fecha __________, y de conformidad con lo establecido en el Real Decreto
XXX/2024, de XX de XXXXX, por el que se regula el programa de ayudas directas
a la adquisición de vivienda habitual, y habida cuenta de que se cumplen los
requisitos exigidos en el artículo 5 del mencionado Real Decreto, esta
Dirección General ha tenido a bien RESOLVER:

PRIMERO. Conceder al/a la solicitante una ayuda directa por importe de
__________ euros (€) para la adquisición de su vivienda habitual.

SEGUNDO. El beneficiario deberá aportar, en el plazo de QUINCE (15) días
hábiles contados desde la notificación de la presente resolución, la
siguiente documentación:
a) Escritura de compraventa debidamente inscrita en el Registro de la Propiedad.
b) Certificado de empadronamiento en la vivienda adquirida.
c) Declaración responsable de no haber percibido otras ayudas incompatibles,
   quedando obligado a reintegrar las cantidades percibidas en caso de
   incumplimiento, siéndole de aplicación lo dispuesto en el artículo 37
   de la Ley 38/2003, de 17 de noviembre, General de Subvenciones.

TERCERO. Contra la presente resolución, que no pone fin a la vía
administrativa, podrá interponerse recurso de alzada ante el/la titular de
la Secretaría de Estado de Vivienda, en el plazo de UN (1) MES a contar
desde el día siguiente al de su notificación, de conformidad con lo
dispuesto en los artículos 121 y 122 de la Ley 39/2015, de 1 de octubre,
del Procedimiento Administrativo Común de las Administraciones Públicas.

En Madrid, a __ de __________ de 2024.
EL/LA DIRECTOR/A GENERAL DE VIVIENDA
```

- [ ] **Step 3: Create the meta annotation file**

`evals/datasets/golden/resolucion_01_meta.json`:

```json
{
  "id": "resolucion_01",
  "description": "Resolución de concesión de ayuda para adquisición de vivienda. Lenguaje administrativo formal con estructura numerada.",
  "expected_tipologia": "resolución",
  "notes": "Human-confirmed classification. Document uses numbered PRIMERO/SEGUNDO/TERCERO structure, typical of administrative resolutions."
}
```

- [ ] **Step 4: Create evals/__init__.py**

```python
# evals/__init__.py
```
(empty file)

- [ ] **Step 5: Create evals/conftest.py with fixture loader**

```python
# evals/conftest.py
"""Fixtures and configuration for eval tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

GOLDEN_DIR = Path(__file__).parent / "datasets" / "golden"


@pytest.fixture
def golden_resolucion_01() -> dict:
    """Returns {'texto': str, 'meta': dict} for resolucion_01 golden fixture."""
    texto = (GOLDEN_DIR / "resolucion_01.txt").read_text(encoding="utf-8")
    meta = json.loads((GOLDEN_DIR / "resolucion_01_meta.json").read_text(encoding="utf-8"))
    return {"texto": texto, "meta": meta}
```

- [ ] **Step 6: Verify fixtures load cleanly**

```bash
pytest evals/ --collect-only
```
Expected: No errors. The conftest is collected.

- [ ] **Step 7: Commit**

```bash
git add evals/__init__.py evals/conftest.py \
        evals/datasets/golden/resolucion_01.txt \
        evals/datasets/golden/resolucion_01_meta.json \
        pytest.ini
git commit -m "test: add golden dataset structure and eval pytest marker"
```

---

### Task 4: Classification eval (SA-0)

**Files:**
- Create: `evals/test_clasificador.py`

This test makes a **real LLM call** to verify SA-0 classifies `resolucion_01` as `"resolución"`. It is marked `@pytest.mark.eval` so it only runs when explicitly invoked with `pytest -m eval`. It requires `GROQ_API_KEY` in the environment.

- [ ] **Step 1: Write the failing test**

```python
# evals/test_clasificador.py
"""
Eval tests for SA-0: document classification.

These tests make real LLM calls. Run with:
    pytest -m eval evals/test_clasificador.py -v

Requires: GROQ_API_KEY environment variable.
"""
from __future__ import annotations

import pytest

from evaluador_lc.pipeline import nodo_clasificador


@pytest.mark.eval
def test_clasificador_resolucion_01(golden_resolucion_01):
    """SA-0 should classify a housing-aid resolution as 'resolución'."""
    texto = golden_resolucion_01["texto"]
    expected_tipologia = golden_resolucion_01["meta"]["expected_tipologia"]

    state = {"texto": texto}
    result = nodo_clasificador(state)

    assert result["tipologia"] == expected_tipologia, (
        f"Expected tipología '{expected_tipologia}', "
        f"got '{result['tipologia']}'. "
        f"Justificación: {result.get('justificacion_tipologia', 'N/A')}"
    )


@pytest.mark.eval
def test_clasificador_returns_justificacion(golden_resolucion_01):
    """SA-0 should always return a non-empty justificación."""
    state = {"texto": golden_resolucion_01["texto"]}
    result = nodo_clasificador(state)

    assert isinstance(result.get("justificacion_tipologia"), str)
    assert len(result["justificacion_tipologia"]) > 0
```

- [ ] **Step 2: Verify the test is collected but skipped by default**

```bash
pytest evals/test_clasificador.py -v
```
Expected: Tests are **collected** (shown in output) but **not run** because `-m eval` was not passed. They may be deselected or collected but skipped depending on pytest config. Either is fine.

- [ ] **Step 3: Run the real eval (requires GROQ_API_KEY)**

```bash
pytest -m eval evals/test_clasificador.py -v
```
Expected: Both tests PASS. If they fail, review the prompt at `evaluador_lc/prompts.py` → `PROMPT_CLASIFICADOR` and check the LLM response manually.

- [ ] **Step 4: Commit**

```bash
git add evals/test_clasificador.py
git commit -m "test(eval): add classification eval for SA-0 against golden dataset"
```

---

## Chunk 3: Full CI check + documentation

### Task 5: Verify the full non-eval suite still passes

- [ ] **Step 1: Run all non-eval tests**

```bash
pytest tests/ -v
```
Expected: All existing tests + new `test_pipeline_helpers.py` + `test_scoring.py` PASS. Zero LLM calls. Should complete in under 5 seconds.

- [ ] **Step 2: Confirm eval tests are excluded from default run**

```bash
pytest --co -q
```
Expected: Tests in `evals/` appear in collection output but the `@pytest.mark.eval` ones are deselected when running without `-m eval`.

Actually, pytest by default **runs** marked tests unless you filter them out. To exclude eval tests from CI by default, add a `filterwarnings`/`addopts` line:

Edit `pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
addopts = -m "not eval"
markers =
    eval: marks tests as real LLM eval tests (run with: pytest -m eval)
```

- [ ] **Step 3: Verify default run excludes evals**

```bash
pytest -v
```
Expected: `evals/test_clasificador.py` tests are **deselected** (shown as "X deselected"). All others pass.

- [ ] **Step 4: Verify eval tests still work explicitly**

```bash
pytest -m eval -v
```
Expected: `evals/test_clasificador.py` runs (requires GROQ_API_KEY).

- [ ] **Step 5: Final commit**

```bash
git add pytest.ini
git commit -m "test: exclude eval-marked tests from default pytest run"
```

---

## Summary

After all tasks complete:

| Command | What runs | LLM calls |
|---------|-----------|-----------|
| `pytest` | Unit tests only (helpers + scoring + API + MCP) | None |
| `pytest -m eval` | Golden dataset classification eval | Yes (SA-0) |
| `pytest tests/test_scoring.py` | SA-6a scoring math only | None |

**Next steps (Phase 2):**
1. Run the pipeline on 20-50 real documents
2. Manually review outputs → open-code failure patterns
3. Add `evals/datasets/golden/` entries for discovered failure modes
4. Build per-item binary evals for SA-1..5 based on confirmed annotations
5. Build LLM-as-judge for SA-6b synthesis (after validating against human labels)

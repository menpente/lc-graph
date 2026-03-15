# evals/test_clasificador.py
"""
Eval tests for SA-0: document classification.

These tests make real LLM calls. Run with:
    .venv/bin/py.test -m eval evals/test_clasificador.py -v

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

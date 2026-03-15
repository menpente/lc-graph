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

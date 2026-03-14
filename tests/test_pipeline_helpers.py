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
    assert _limpiar_json(raw) == '{"key": "value"}'


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

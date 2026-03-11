from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


def _make_informe_dict() -> dict:
    return {
        "puntuacion": {
            "puntuacion_general": 75.0,
            "secciones": [
                {
                    "seccion": 1,
                    "nombre": "Facilita la localización",
                    "total_evaluables": 4,
                    "total_si": 3,
                    "total_no": 1,
                    "total_no_compete": 0,
                    "porcentaje": 75.0,
                }
            ],
        },
        "puntos_fuertes": ["Estructura clara"],
        "areas_mejora": ["Simplificar vocabulario"],
        "resumen_narrativo": "El documento cumple parcialmente.",
        "tabla_detallada": [],
    }


def _make_mock_client(informe_dict: dict) -> AsyncMock:
    mock_response = MagicMock()
    mock_response.json.return_value = informe_dict
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


async def test_do_evaluate_returns_formatted_string():
    # Tests the inner helper directly — decoupled from @mcp.tool() decorator behaviour
    from evaluador_lc.mcp_server import _do_evaluate

    mock_client = _make_mock_client(_make_informe_dict())

    with patch("evaluador_lc.mcp_server.httpx.AsyncClient", return_value=mock_client):
        result = await _do_evaluate("Texto de prueba")

    # Sentinel strings confirmed from pipeline.py:312-313
    assert "PUNTUACIÓN GENERAL" in result
    assert "75.0%" in result


async def test_do_evaluate_posts_to_configured_url():
    from evaluador_lc.mcp_server import _do_evaluate

    mock_client = _make_mock_client(_make_informe_dict())

    with patch("evaluador_lc.mcp_server.httpx.AsyncClient", return_value=mock_client):
        await _do_evaluate("doc text", url="http://test-host:9000")

    mock_client.post.assert_called_once_with(
        "http://test-host:9000/evaluate", json={"texto": "doc text"}
    )


async def test_do_evaluate_raises_on_http_error():
    from evaluador_lc.mcp_server import _do_evaluate

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("evaluador_lc.mcp_server.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(httpx.HTTPStatusError):
            await _do_evaluate("bad input")

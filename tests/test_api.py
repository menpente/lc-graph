from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from evaluador_lc.models import (
    InformeFinal,
    PuntuacionGlobal,
    PuntuacionSeccion,
)


def _make_informe() -> InformeFinal:
    puntuacion = PuntuacionGlobal(
        puntuacion_general=80.0,
        secciones=[
            PuntuacionSeccion(
                seccion=1,
                nombre="Facilita la localización",
                total_evaluables=5,
                total_si=4,
                total_no=1,
                total_no_compete=0,
                porcentaje=80.0,
            )
        ],
    )
    return InformeFinal(
        puntuacion=puntuacion,
        puntos_fuertes=["Buen formato"],
        areas_mejora=["Mejorar claridad"],
        resumen_narrativo="Documento correcto.",
        tabla_detallada=[],
    )


@pytest.fixture
def client():
    from evaluador_lc.api import app
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_evaluate_returns_informe_final(client):
    informe = _make_informe()
    mock_result = {"informe_final": informe}

    with patch("evaluador_lc.api.crear_grafo") as mock_crear:
        mock_grafo = MagicMock()
        mock_grafo.invoke.return_value = mock_result
        mock_crear.return_value = mock_grafo

        r = client.post("/evaluate", json={"texto": "Texto de prueba"})

    assert r.status_code == 200
    data = r.json()
    assert data["puntuacion"]["puntuacion_general"] == 80.0
    assert data["puntos_fuertes"] == ["Buen formato"]


def test_evaluate_calls_pipeline_with_texto(client):
    informe = _make_informe()
    mock_result = {"informe_final": informe}

    with patch("evaluador_lc.api.crear_grafo") as mock_crear:
        mock_grafo = MagicMock()
        mock_grafo.invoke.return_value = mock_result
        mock_crear.return_value = mock_grafo

        client.post("/evaluate", json={"texto": "Mi documento"})

        mock_grafo.invoke.assert_called_once_with({"texto": "Mi documento"})


def test_evaluate_empty_texto_returns_422(client):
    r = client.post("/evaluate", json={"texto": ""})
    assert r.status_code == 422


def test_evaluate_pipeline_error_returns_500():
    from evaluador_lc.api import app

    # raise_server_exceptions=False makes TestClient return the HTTP response
    # instead of re-raising the exception in the test process.
    error_client = TestClient(app, raise_server_exceptions=False)

    with patch("evaluador_lc.api.crear_grafo") as mock_crear:
        mock_grafo = MagicMock()
        mock_grafo.invoke.side_effect = RuntimeError("LLM failure")
        mock_crear.return_value = mock_grafo

        r = error_client.post("/evaluate", json={"texto": "Texto"})

    assert r.status_code == 500

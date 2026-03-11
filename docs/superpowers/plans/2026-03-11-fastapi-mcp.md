# FastAPI + MCP Proxy Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a FastAPI HTTP service exposing the LangGraph pipeline, and a lightweight stdio MCP server that proxies to it.

**Architecture:** `evaluador_lc/api.py` is a FastAPI app with `POST /evaluate` (runs pipeline via `asyncio.to_thread`), `GET /health`, and a generic 500 exception handler. `evaluador_lc/mcp_server.py` is a stdio MCP server with one tool (`evaluate_document`) backed by a testable helper `_do_evaluate` that calls the FastAPI service via `httpx.AsyncClient`. No existing pipeline code is modified.

**Tech Stack:** FastAPI, uvicorn, httpx, mcp (FastMCP), pytest, pytest-asyncio

---

## Chunk 1: Dependencies & Test Scaffold

### Task 1: Add new dependencies to pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add runtime and test dependencies**

Edit `pyproject.toml` so it reads:

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
    "langchain-groq",
    "langgraph",
    "pydantic",
    "fastapi",
    "uvicorn[standard]",
    "httpx",
    "mcp",
]

[project.optional-dependencies]
test = [
    "pytest",
    "pytest-asyncio",
]

[project.urls]
Homepage = "https://github.com/rubendelafuente/lc-graph"
"Live Demo" = "https://rubendelafuente.github.io/lc-graph/"
```

Note: `httpx` is a runtime dep (needed by `mcp_server.py`) and also required by `fastapi.testclient.TestClient` (FastAPI >= 0.87 uses httpx as the test transport backend).

- [ ] **Step 2: Install the new dependencies**

```bash
pip install -e ".[test]"
```

Expected: packages install without errors; `fastapi`, `uvicorn`, `httpx`, `mcp`, `pytest`, `pytest-asyncio` are importable.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add fastapi, uvicorn, httpx, mcp and test deps"
```

---

### Task 2: Create test directory scaffold

**Files:**
- Create: `tests/__init__.py`
- Create: `pytest.ini`

- [ ] **Step 1: Create tests package**

```bash
mkdir tests
touch tests/__init__.py
```

- [ ] **Step 2: Create pytest.ini**

Create `pytest.ini` at the repo root:

```ini
[pytest]
asyncio_mode = auto
```

This enables `pytest-asyncio` auto mode so `async def` test functions run without needing `@pytest.mark.asyncio` decorators.

- [ ] **Step 3: Verify pytest is runnable**

```bash
pytest tests/ -v
```

Expected: `no tests ran` — no errors, just nothing collected yet.

- [ ] **Step 4: Commit**

```bash
git add tests/__init__.py pytest.ini
git commit -m "chore: add test scaffold and pytest config"
```

---

## Chunk 2: FastAPI App

### Task 3: Build the FastAPI app with TDD

**Files:**
- Create: `tests/test_api.py`
- Create: `evaluador_lc/api.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_api.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `evaluador_lc.api` does not exist yet.

- [ ] **Step 3: Implement api.py**

Create `evaluador_lc/api.py`:

```python
import asyncio

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from evaluador_lc.models import InformeFinal
from evaluador_lc.pipeline import crear_grafo

app = FastAPI(title="Evaluador Lenguaje Claro")


class EvaluateRequest(BaseModel):
    texto: str = Field(..., min_length=1)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/evaluate", response_model=InformeFinal)
async def evaluate(request: EvaluateRequest):
    try:
        grafo = crear_grafo()
        resultado = await asyncio.to_thread(grafo.invoke, {"texto": request.texto})
        return resultado["informe_final"]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
```

Note: `@app.exception_handler(Exception)` is intentionally NOT used — Starlette's `ServerErrorMiddleware` intercepts unhandled route exceptions before custom exception handlers fire. A try/except in the route is the reliable pattern.

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_api.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Smoke-test the server manually (optional but recommended)**

In one terminal:
```bash
GROQ_API_KEY=your-key uvicorn evaluador_lc.api:app --port 8000
```

In another:
```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 6: Commit**

```bash
git add evaluador_lc/api.py tests/test_api.py
git commit -m "feat: add FastAPI service with /evaluate and /health endpoints"
```

---

## Chunk 3: MCP Server

### Task 4: Build the MCP stdio server with TDD

**Files:**
- Create: `tests/test_mcp_server.py`
- Create: `evaluador_lc/mcp_server.py`

**Implementation note on `@mcp.tool()` and testability:**
`FastMCP`'s `@mcp.tool()` decorator registers the function with the MCP server. Its behaviour on the callable itself varies across SDK versions — it may or may not preserve the coroutine as directly `await`-able. To avoid coupling tests to that detail, the HTTP logic lives in a private helper `_do_evaluate` that tests call directly. The `@mcp.tool()`-decorated `evaluate_document` is a one-liner that delegates to it.

**Sentinel string verification:**
Tests assert `"PUNTUACIÓN GENERAL"` and `"75.0%"` appear in the formatted output. These are guaranteed by `formatear_informe` in `pipeline.py:312-313`:
```python
lineas.append(f"  PUNTUACIÓN GENERAL: {p.puntuacion_general}%")
```
So `"PUNTUACIÓN GENERAL"` and `"75.0%"` will both be present for a score of 75.0.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_mcp_server.py`:

```python
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
    import evaluador_lc.mcp_server as mod

    mock_client = _make_mock_client(_make_informe_dict())

    original_url = mod.FASTAPI_URL
    mod.FASTAPI_URL = "http://test-host:9000"
    try:
        with patch("evaluador_lc.mcp_server.httpx.AsyncClient", return_value=mock_client):
            await _do_evaluate("doc text")
    finally:
        mod.FASTAPI_URL = original_url

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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_mcp_server.py -v
```

Expected: `ImportError` — `evaluador_lc.mcp_server` does not exist yet.

- [ ] **Step 3: Implement mcp_server.py**

Create `evaluador_lc/mcp_server.py`:

```python
import os

import httpx
from mcp.server.fastmcp import FastMCP

from evaluador_lc.models import InformeFinal
from evaluador_lc.pipeline import formatear_informe

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

mcp = FastMCP("evaluador-lc")


async def _do_evaluate(texto: str) -> str:
    """Core HTTP logic — separated from @mcp.tool() for testability."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{FASTAPI_URL}/evaluate", json={"texto": texto})
        r.raise_for_status()
        informe = InformeFinal(**r.json())
        return formatear_informe(informe)


@mcp.tool()
async def evaluate_document(texto: str) -> str:
    """Evalúa un documento administrativo en español según criterios de lenguaje claro.

    Returns a formatted plain-text report with scores, strengths, areas for
    improvement, and a detailed per-criterion table.
    """
    return await _do_evaluate(texto)


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
pytest tests/ -v
```

Expected: all 8 tests PASS (5 from `test_api.py`, 3 from `test_mcp_server.py`).

- [ ] **Step 5: Commit**

```bash
git add evaluador_lc/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: add stdio MCP server proxying to FastAPI"
```

---

## Usage Reference

**Start the API server:**
```bash
GROQ_API_KEY=your-key uvicorn evaluador_lc.api:app --port 8000
```

**Configure MCP in Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "evaluador-lc": {
      "command": "python",
      "args": ["-m", "evaluador_lc.mcp_server"],
      "env": {
        "FASTAPI_URL": "http://localhost:8000",
        "GROQ_API_KEY": "your-key"
      }
    }
  }
}
```

**Configure MCP in Claude Code** (`.claude/settings.json`):
```json
{
  "mcpServers": {
    "evaluador-lc": {
      "command": "python",
      "args": ["-m", "evaluador_lc.mcp_server"],
      "env": {
        "FASTAPI_URL": "http://localhost:8000"
      }
    }
  }
}
```

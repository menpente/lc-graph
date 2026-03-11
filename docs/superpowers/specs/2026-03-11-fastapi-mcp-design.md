# FastAPI Core + MCP Proxy Design

**Date:** 2026-03-11
**Status:** Approved

## Summary

Add a FastAPI HTTP service as the primary interface to the `evaluador_lc` LangGraph pipeline, and a lightweight stdio MCP server that proxies to it. Existing pipeline code is unchanged.

## Architecture

```
MCP Client (Claude Desktop / Claude Code)
        │ stdio (MCP protocol)
mcp_server.py  (stdio MCP server)
  • one tool: evaluate_document(texto)
  • calls FastAPI via httpx.AsyncClient
        │ HTTP POST /evaluate
api.py  (FastAPI, uvicorn)
  POST /evaluate  →  InformeFinal JSON
  GET  /health    →  {"status": "ok"}
  • runs pipeline in asyncio.to_thread
        │ Python call
evaluador_lc/pipeline.py  (LangGraph, unchanged)
```

**New files:** `evaluador_lc/api.py`, `evaluador_lc/mcp_server.py`
**New deps:** `fastapi`, `uvicorn[standard]`, `httpx`, `mcp`
**Unchanged:** all existing `evaluador_lc/` code

## API Contract

### `POST /evaluate`

Request:
```json
{ "texto": "Texto del documento administrativo..." }
```

Response 200 — `InformeFinal` serialized directly (no envelope):
```json
{
  "puntuacion": { "puntuacion_general": 72.5, "secciones": [...] },
  "puntos_fuertes": ["..."],
  "areas_mejora": ["..."],
  "resumen_narrativo": "...",
  "tabla_detallada": [...]
}
```

Response 422 — validation error (empty `texto`)
Response 500 — pipeline failure (LLM error, etc.)

### `GET /health`

```json
{ "status": "ok" }
```

## MCP Tool

**Name:** `evaluate_document`
**Input:** `texto: str`
**Output:** formatted report string (via `formatear_informe`) — readable text is more useful to an LLM than raw JSON
**Config:** reads `FASTAPI_URL` from env (default: `http://localhost:8000`)

## Key Implementation Details

### api.py

The pipeline is synchronous (blocking LLM calls). It runs in a thread pool via `asyncio.to_thread` to avoid blocking the event loop. The graph is constructed per-request — it is cheap and stateless, avoiding shared mutable state between concurrent requests.

```python
@app.post("/evaluate", response_model=InformeFinal)
async def evaluate(request: EvaluateRequest):
    grafo = crear_grafo()
    resultado = await asyncio.to_thread(grafo.invoke, {"texto": request.texto})
    return resultado["informe_final"]
```

### mcp_server.py

Thin proxy, ~50 lines. Uses `httpx.AsyncClient` with a 120s timeout (pipeline can take 10-30s).

```python
@mcp.tool()
async def evaluate_document(texto: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{FASTAPI_URL}/evaluate", json={"texto": texto})
        r.raise_for_status()
        informe = InformeFinal(**r.json())
        return formatear_informe(informe)
```

### Running

```bash
# Start the API server
uvicorn evaluador_lc.api:app --port 8000

# Start the MCP server (stdio)
python -m evaluador_lc.mcp_server
```

## Error Handling

HTTP 500 from FastAPI propagates as `httpx.HTTPStatusError` in the MCP server — the MCP client sees a tool error with the message. No retry logic.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Endpoint style | Synchronous | MCP proxy awaits result anyway; job polling adds complexity with no benefit |
| Endpoints | `/evaluate` + `/health` | Health check needed for deployment; no value in splitting classification |
| MCP transport | stdio | Standard for Claude Desktop/Code; no extra port or auth needed |
| File location | Same package | Codebase is small; two thin files don't warrant separate packages |
| Approach | FastAPI native async + httpx proxy | Clean separation, concurrent-request capable, MCP stays minimal |

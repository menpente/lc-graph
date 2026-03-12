# LangSmith Observability Design

**Date:** 2026-03-12
**Status:** Approved

## Summary

Add LangSmith tracing to both the FastAPI service and the HTML browser demo. The FastAPI service uses automatic LangChain/LangGraph tracing via environment variables. The HTML demo sends traces directly to the LangSmith REST API with the key obfuscated via Base64 split in page source.

## Part 1: FastAPI Service

### What Changes

| File | Action |
|---|---|
| `pyproject.toml` | Add `langsmith` as explicit runtime dependency |
| `.env.example` | Add 3 LangSmith env vars |

### Environment Variables

Add to `.env.example`:

```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__your_key_here
LANGCHAIN_PROJECT=evaluador-lc
```

No code changes needed. `api.py` already calls `load_dotenv()` at startup. LangChain/LangGraph automatically traces every `grafo.invoke()` call when these vars are set — all 7 LLM calls, parallel branches, inputs/outputs, latencies, token counts appear in LangSmith.

## Part 2: HTML Demo (`docs/index.html`)

### What Changes

| File | Action |
|---|---|
| `docs/index.html` | Add LangSmith tracing via REST API + obfuscated key |

### Key Obfuscation

The LangSmith API key is Base64-encoded and split across 3 variables in the JS source. It is reassembled at call time using `atob()`:

```javascript
const _a = '<fragment1>';
const _b = '<fragment2>';
const _c = '<fragment3>';
const _lsk = () => atob(_a + _b + _c);
```

**Security note:** This is obfuscation only — not encryption. A determined user with DevTools can recover the key. The risk is limited: a LangSmith key only allows writing traces to the account, not reading sensitive data or incurring financial costs.

### Tracing Implementation

Two `fetch` calls to the LangSmith REST API wrap each `ejecutarPipeline` invocation:

Both calls use header `x-api-key: <langsmith_key>` and `Content-Type: application/json`.

1. **`POST https://api.smith.langchain.com/runs`** — at pipeline start, creates the run with:
   - `id`: UUID generated via `crypto.randomUUID()` (requires HTTPS — met by GitHub Pages)
   - `run_type: "chain"`
   - `name: "evaluador-lc"`
   - `inputs: { texto: texto.slice(0, 500) }` — truncated to avoid large payloads
   - `start_time`: ISO timestamp

2. **`PATCH https://api.smith.langchain.com/runs/{id}`** — at pipeline end, patches with:
   - `outputs: { puntuacion_general, tipologia }` — scores only, not full report (only on success)
   - `end_time`: ISO timestamp
   - `error`: error message string (only on failure)

### Error Handling

Tracing is best-effort. All LangSmith `fetch` calls are wrapped in `try/catch` that silently swallows errors — a LangSmith outage or network issue never blocks or breaks the demo.

### Run ID

A UUID v4 is generated client-side for each run using `crypto.randomUUID()`.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| FastAPI tracing | Env vars only | LangGraph auto-traces; no code changes needed |
| Demo tracing | Direct REST API fetch | No SDK dependency, HTML stays self-contained |
| Obfuscation | Base64 split (3 parts) | Defeats casual page-source inspection, minimal complexity |
| Trace payload | Truncated inputs, scores only | Avoids large payloads; prompts stay hidden |
| Error handling | Silent best-effort | Tracing must never break the demo |

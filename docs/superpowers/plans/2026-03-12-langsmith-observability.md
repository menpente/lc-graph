# LangSmith Observability Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add LangSmith tracing to the FastAPI service (via env vars) and to the HTML browser demo (via direct REST API calls with an obfuscated hardcoded key).

**Architecture:** FastAPI/LangGraph traces automatically when `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` are set — no code changes needed, only `pyproject.toml` and `.env.example`. The HTML demo sends traces directly to the LangSmith REST API from the browser using `fetch`, with the API key Base64-encoded and split across 3 JS variables to defeat casual page-source inspection.

**Tech Stack:** Python (pyproject.toml, uv), LangSmith REST API, vanilla JavaScript (fetch, crypto.randomUUID)

---

## Chunk 1: FastAPI service — langsmith dependency + env vars

### Task 1: Add langsmith to pyproject.toml and env vars to .env.example

**Files:**
- Modify: `pyproject.toml` (dependencies list)
- Modify: `.env.example` (add 3 LangSmith vars)

- [ ] **Step 1: Add langsmith to pyproject.toml dependencies**

Open `pyproject.toml`. In the `dependencies` list (currently ends with `"mcp"`), add `"langsmith"`:

```toml
dependencies = [
    "langchain-groq",
    "langgraph",
    "pydantic",
    "fastapi",
    "uvicorn[standard]",
    "httpx",
    "mcp",
    "langsmith",
]
```

- [ ] **Step 2: Add LangSmith env vars to .env.example**

Open `.env.example` (currently has 2 lines). Append the 3 LangSmith vars so the full file reads:

```
GROQ_API_KEY=your-groq-api-key-here
FASTAPI_URL=http://localhost:8000
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__your_key_here
LANGCHAIN_PROJECT=evaluador-lc
```

- [ ] **Step 3: Install langsmith into the venv**

```bash
uv pip install langsmith
```

Expected: `Successfully installed langsmith-...`

- [ ] **Step 4: Verify import works**

```bash
.venv/bin/python -c "import langsmith; print('ok')"
```

Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .env.example
git commit -m "chore: add langsmith dep and LangSmith env vars to .env.example"
```

---

## Chunk 2: HTML demo — LangSmith REST API tracing

### Task 2: Add tracing to docs/index.html

**Files:**
- Modify: `docs/index.html`

The tracing code goes in two places:
1. Before the `// D. Orchestrator` section (~line 1103): add the obfuscated key constants and the `lsTrace` helper.
2. Around the `ejecutarPipeline` call (~line 1424): wrap it with `POST /runs` before and `PATCH /runs/{id}` after.

**Preparing the obfuscated key fragments (do this before editing the file):**

You need the user's actual LangSmith API key (format: `ls__xxxxxxxx...`). In a browser DevTools console or Node REPL:

```javascript
const encoded = btoa("ls__YOUR_ACTUAL_KEY_HERE");
// Split into 3 roughly equal parts
const third = Math.ceil(encoded.length / 3);
const a = encoded.slice(0, third);
const b = encoded.slice(third, third * 2);
const c = encoded.slice(third * 2);
console.log({a, b, c});
// Verify round-trip:
console.log(atob(a + b + c)); // should print original key
```

Use the values of `a`, `b`, `c` in the code below.

- [ ] **Step 1: Add key constants and lsTrace helper before the Orchestrator section**

In `docs/index.html`, find this line (around line 1103):

```javascript
// ═══════════════════════════════════════════════════════════════════════════
// D. Orchestrator
```

Insert the following block **immediately before** that comment:

```javascript
// ═══════════════════════════════════════════════════════════════════════════
// LangSmith tracing (best-effort, errors are silently swallowed)
// ═══════════════════════════════════════════════════════════════════════════

const _a = 'FRAGMENT_A_HERE';
const _b = 'FRAGMENT_B_HERE';
const _c = 'FRAGMENT_C_HERE';
const _lsk = () => atob(_a + _b + _c);

async function lsTrace(runId, phase, data) {
  try {
    const headers = { 'Content-Type': 'application/json', 'x-api-key': _lsk() };
    if (phase === 'start') {
      await fetch('https://api.smith.langchain.com/runs', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          id: runId,
          run_type: 'chain',
          name: 'evaluador-lc',
          inputs: { texto: data.texto.slice(0, 500) },
          start_time: data.start_time,
        }),
      });
    } else {
      const body = { end_time: new Date().toISOString() };
      if (data.error) {
        body.error = data.error;
      } else {
        body.outputs = { puntuacion_general: data.puntuacion_general, tipologia: data.tipologia };
      }
      await fetch(`https://api.smith.langchain.com/runs/${runId}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(body),
      });
    }
  } catch (_) {
    // Tracing is best-effort — never block the demo
  }
}

```

Replace `FRAGMENT_A_HERE`, `FRAGMENT_B_HERE`, `FRAGMENT_C_HERE` with the actual Base64 fragments computed above.

- [ ] **Step 2: Verify the key round-trip in browser DevTools**

After inserting the code, open the HTML file in a browser and run in DevTools console:

```javascript
console.log(_lsk());
```

Expected: your original LangSmith API key printed. If not, recheck the fragment split.

- [ ] **Step 3: Wrap the ejecutarPipeline call with tracing**

Find this block in `docs/index.html` (around line 1423):

```javascript
    try {
      const informe = await ejecutarPipeline(texto, apiKey);
      renderizarInforme(informe);
    } catch (err) {
      // Mark any still-running steps as error
      document.querySelectorAll('.step.running').forEach(el => setStep(Number(el.dataset.step), 'error'));
      showError(err.message);
    } finally {
      btn.disabled = false;
    }
```

Replace it with:

```javascript
    const _runId = crypto.randomUUID();
    await lsTrace(_runId, 'start', { texto, start_time: new Date().toISOString() });

    try {
      const informe = await ejecutarPipeline(texto, apiKey);
      renderizarInforme(informe);
      await lsTrace(_runId, 'end', {
        puntuacion_general: informe.puntuacion?.puntuacion_general ?? null,
        tipologia: informe.tipologia ?? null,
      });
    } catch (err) {
      await lsTrace(_runId, 'end', { error: err.message });
      // Mark any still-running steps as error
      document.querySelectorAll('.step.running').forEach(el => setStep(Number(el.dataset.step), 'error'));
      showError(err.message);
    } finally {
      btn.disabled = false;
    }
```

- [ ] **Step 4: Smoke-test in browser**

Open `docs/index.html` in a browser (or open the GitHub Pages URL if already deployed), paste a short Spanish document snippet, enter your Groq key, and click Evaluar.

After the pipeline completes:
1. Open browser DevTools → Network tab → filter by `smith.langchain.com`
2. Verify there are 2 requests: one POST (status 200) and one PATCH (status 200)
3. In LangSmith dashboard, confirm the run appears under project `evaluador-lc`

- [ ] **Step 5: Commit**

```bash
git add docs/index.html
git commit -m "feat: add LangSmith tracing to HTML demo with obfuscated key"
```

- [ ] **Step 6: Push**

```bash
git push origin main
```

Expected: push succeeds, GitHub Pages will redeploy automatically within ~1 minute.

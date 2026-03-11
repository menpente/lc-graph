# Hide Prompts Design

**Date:** 2026-03-11
**Status:** Approved

## Summary

Remove `evaluador_lc/prompts.py` from the public repo and its entire git history. The prompts contain linguistic expertise shared privately and should not be public. A placeholder example file is committed so contributors know the expected structure.

## Scope

**Partial protection (Option B):** The Python repo prompts are hidden. The browser demo (`docs/index.html`) contains a JavaScript copy of the prompts in its source — this remains public and is an accepted trade-off.

## What Changes

| File | Action |
|---|---|
| `evaluador_lc/prompts.py` | Removed from repo + history. Added to `.gitignore`. |
| `evaluador_lc/prompts.py.example` | New — committed placeholder with same exports, empty strings. |
| `.gitignore` | Add `evaluador_lc/prompts.py` entry. |
| `evaluador_lc/pipeline.py` | Import guard: raises `RuntimeError` with clear message if `prompts.py` missing. |

## Example File

`evaluador_lc/prompts.py.example` — committed, shows structure without content:

```python
# Copy this file to prompts.py and fill in the prompts.
# Contact the author to obtain the actual prompt content.

PROMPT_CLASIFICADOR = ""

PROMPT_SINTETIZADOR = ""

PROMPTS_SECCIONES = {
    1: "",
    2: "",
    3: "",
    4: "",
    5: "",
}
```

## Import Guard

Replaces the current bare imports in `pipeline.py`:

```python
try:
    from evaluador_lc.prompts import (
        PROMPT_CLASIFICADOR,
        PROMPT_SINTETIZADOR,
        PROMPTS_SECCIONES,
    )
except ImportError:
    raise RuntimeError(
        "evaluador_lc/prompts.py not found. "
        "Copy prompts.py.example to prompts.py and fill in the prompt content."
    )
```

## Git History Rewrite

Use BFG Repo Cleaner to remove `evaluador_lc/prompts.py` from every commit in history, then force-push.

**Steps (order matters):**
1. Add `evaluador_lc/prompts.py` to `.gitignore` and commit — do this **before** BFG so the gitignore is in the clean state
2. Download BFG jar (`bfg-1.14.0.jar`)
3. Make a fresh bare clone: `git clone --mirror <repo-url> repo.git`
4. Run BFG targeting the exact path to avoid accidentally deleting other `prompts.py` files: `java -jar bfg.jar --delete-files 'prompts.py' repo.git`
5. Clean refs inside the bare clone: `cd repo.git && git reflog expire --expire=now --all && git gc --prune=now --aggressive`
6. Force-push: `git push --force`
7. Verify removal: `git log --all --oneline -- evaluador_lc/prompts.py` should return nothing

**After force-push — local clone instructions:**
```bash
git pull --rebase
cp evaluador_lc/prompts.py.example evaluador_lc/prompts.py
# fill in actual prompt content
```

**Side effects:**
- All commit SHAs are rewritten
- Anyone with a local clone must re-clone or rebase
- GitHub cached views take ~24h to fully clear
- `prompts.py` stays on disk locally (untracked, gitignored)

## What Stays Public

The module's export names (`PROMPT_CLASIFICADOR`, `PROMPTS_SECCIONES`, `PROMPT_SINTETIZADOR`) are visible in the example file and pipeline imports. Only the prompt *content* is hidden.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Approach | Gitignore + example file | Simplest, conventional, easy to share out-of-band |
| History tool | BFG Repo Cleaner | Faster and safer than git filter-branch |
| Demo prompts | Left as-is | Accepted trade-off (Option B) |

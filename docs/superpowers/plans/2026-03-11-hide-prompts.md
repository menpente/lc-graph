# Hide Prompts Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove `evaluador_lc/prompts.py` and its content from the public repo and its entire git history, replacing it with a placeholder example file and an import guard in the pipeline.

**Architecture:** Add `evaluador_lc/prompts.py` to `.gitignore` and commit a `prompts.py.example` placeholder. Add an import guard in `pipeline.py` that raises a clear `RuntimeError` if `prompts.py` is missing. Then use BFG Repo Cleaner to scrub the file from all git history and force-push.

**Tech Stack:** Python, BFG Repo Cleaner (Java jar), git

---

## Chunk 1: Code Changes

### Task 1: Add prompts.py to .gitignore and create example file

**Files:**
- Modify: `.gitignore`
- Create: `evaluador_lc/prompts.py.example`

- [ ] **Step 1: Add prompts.py to .gitignore**

Open `.gitignore` and add this line in the `# Python` section:

```
evaluador_lc/prompts.py
```

The full `# Python` section should now look like:

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/
.eggs/
evaluador_lc/prompts.py
```

- [ ] **Step 2: Create the example file**

Create `evaluador_lc/prompts.py.example` with exactly this content:

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

- [ ] **Step 3: Verify prompts.py is now ignored**

```bash
git check-ignore -v evaluador_lc/prompts.py
```

Expected output: `.gitignore:N:evaluador_lc/prompts.py  evaluador_lc/prompts.py`

- [ ] **Step 4: Untrack prompts.py from the index (remove from HEAD without deleting from disk)**

```bash
git rm --cached evaluador_lc/prompts.py
```

Expected: `rm 'evaluador_lc/prompts.py'`

Verify the file still exists on disk:
```bash
ls evaluador_lc/prompts.py
```

Expected: file is present. `git rm --cached` only removes it from git's index, not from disk.

- [ ] **Step 5: Commit**

```bash
git add .gitignore evaluador_lc/prompts.py.example
git commit -m "chore: gitignore prompts.py and add placeholder example"
```

Note: `prompts.py` is gone from HEAD and from all future commits. It still appears in past history — that gets fixed in Task 3.

---

### Task 2: Add import guard to pipeline.py

**Files:**
- Modify: `evaluador_lc/pipeline.py:35-39`
- Test: `tests/test_pipeline_import_guard.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_pipeline_import_guard.py`:

```python
import sys
from unittest.mock import patch

import pytest


def test_missing_prompts_raises_runtime_error():
    """pipeline raises RuntimeError with helpful message when prompts.py is missing."""
    # Remove cached modules so we get a fresh import
    for key in list(sys.modules.keys()):
        if "evaluador_lc" in key:
            del sys.modules[key]

    with patch.dict("sys.modules", {"evaluador_lc.prompts": None}):
        with pytest.raises(RuntimeError, match="prompts.py.example"):
            import evaluador_lc.pipeline
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
.venv/bin/pytest tests/test_pipeline_import_guard.py -v
```

Expected: FAIL — the current pipeline imports prompts without a guard so no `RuntimeError` is raised.

- [ ] **Step 3: Replace the bare import in pipeline.py**

In `evaluador_lc/pipeline.py`, replace lines 35-39:

```python
from evaluador_lc.prompts import (
    PROMPT_CLASIFICADOR,
    PROMPT_SINTETIZADOR,
    PROMPTS_SECCIONES,
)
```

With:

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

- [ ] **Step 4: Run the test to verify it passes**

```bash
.venv/bin/pytest tests/test_pipeline_import_guard.py -v
```

Expected: PASS.

- [ ] **Step 5: Run the full test suite to verify no regressions**

```bash
.venv/bin/pytest tests/ -v
```

Expected: all 9 tests PASS (8 existing + 1 new).

- [ ] **Step 6: Commit**

```bash
git add evaluador_lc/pipeline.py tests/test_pipeline_import_guard.py
git commit -m "feat: add import guard for missing prompts.py"
```

- [ ] **Step 7: Push**

```bash
git push origin main
```

---

## Chunk 2: History Rewrite

### Task 3: Remove prompts.py from git history with BFG

**Prerequisites:** Java must be installed (`java -version`). Tasks 1 and 2 must be committed and pushed.

**Files:** No source files change — this rewrites git history only.

- [ ] **Step 1: Download BFG Repo Cleaner**

```bash
curl -L https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar -o /tmp/bfg.jar
```

Verify: `java -jar /tmp/bfg.jar --version` should print `BFG Repo-Cleaner ...`

- [ ] **Step 2: Create a fresh bare clone**

Work in a temp directory outside the repo:

```bash
cd /tmp
git clone --mirror https://github.com/menpente/lc-graph.git lc-graph-mirror.git
```

Expected: `lc-graph-mirror.git/` directory created.

- [ ] **Step 3: Run BFG to delete prompts.py from all history**

```bash
java -jar /tmp/bfg.jar --delete-files 'prompts.py' /tmp/lc-graph-mirror.git
```

Expected output includes:
```
Deleted files:
    prompts.py ...
```

Note: BFG matches on filename only. The only `prompts.py` in this repo is `evaluador_lc/prompts.py`. BFG will not touch the current HEAD commit (it only rewrites history, not the working tree).

- [ ] **Step 4: Clean up refs in the bare clone**

```bash
cd /tmp/lc-graph-mirror.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

- [ ] **Step 5: Verify the file is gone from history**

```bash
git log --all --oneline -- evaluador_lc/prompts.py
```

Expected: no output (empty). If anything is printed, BFG did not fully remove it — do not proceed.

- [ ] **Step 6: Force-push the rewritten history**

```bash
git push --force
```

Expected: all branches pushed successfully.

- [ ] **Step 7: Verify on the local working repo**

Back in `/Users/rubendelafuente/lc-graph`:

```bash
git fetch --all
git log --all --oneline -- evaluador_lc/prompts.py
```

Expected: no output.

Also verify `prompts.py` is still on disk (untracked, gitignored):

```bash
ls evaluador_lc/prompts.py
git status evaluador_lc/prompts.py
```

Expected: file exists, `git status` shows nothing (gitignored).

- [ ] **Step 8: Update local repo to match rewritten history**

```bash
cd /Users/rubendelafuente/lc-graph
git fetch origin
git reset --hard origin/main
```

---

## Post-Implementation Notes

Anyone else with a local clone of this repo must:
```bash
git fetch origin
git reset --hard origin/main
cp evaluador_lc/prompts.py.example evaluador_lc/prompts.py
# fill in actual prompt content
```

GitHub's cached commit views may still show the old content for up to 24 hours.

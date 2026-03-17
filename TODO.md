# TODO

## Evals Phase 2

Run the pipeline on 20–50 real documents, manually review outputs, add golden annotations for discovered failure patterns.

### Steps

1. Run the pipeline on 20–50 real Spanish administrative documents
2. Manually review outputs (open coding — write down what's wrong)
3. Group failure notes into categories (axial coding)
4. Add golden fixtures to `evals/datasets/golden/` for each discovered failure mode
5. Add per-item binary evals for SA-1..5 based on confirmed annotations
6. Build LLM-as-judge for SA-6b synthesis quality (after validating against human labels with 100+ examples)

### Commands

```bash
.venv/bin/py.test               # 30 unit tests, no LLM calls
.venv/bin/py.test -m eval       # SA-0 classification eval (needs GROQ_API_KEY)
```

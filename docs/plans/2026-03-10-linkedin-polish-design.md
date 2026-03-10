# Design: LinkedIn Portfolio Polish

**Date:** 2026-03-10
**Goal:** Polish `lc-graph` repo for LinkedIn featuring — clean structure, English-primary README, live demo via GitHub Pages.

---

## Target audiences

- Software / ML engineers — read code, care about architecture and tech stack
- Domain experts (NLP, linguistics, public administration) — care about the problem and live demo

---

## Repo structure (after polish)

```
lc-graph/
├── evaluador_lc/          # Python package
│   ├── __init__.py
│   ├── main.py
│   ├── pipeline.py
│   ├── models.py
│   └── prompts.py
├── docs/
│   ├── index.html         # renamed from evaluador-lc.html → GitHub Pages live demo
│   └── walkthrough.md     # moved from root
├── pyproject.toml         # modern packaging (new)
├── .gitignore             # new
├── LICENSE                # MIT (new)
└── README.md              # English-primary overhaul
```

**Deleted:** `evaluador-lc-plan.md` (internal planning doc, not portfolio material)

---

## README structure

1. Title + one-line tagline
2. Badges: Python 3.9+ | LangGraph | Claude | MIT | Live Demo
3. Architecture diagram (ASCII) + 7-call breakdown
4. Live demo link (GitHub Pages)
5. Sample output (fenced code block)
6. Quickstart (3-command install + run)
7. Python API snippet
8. Secciones evaluadas table (Spanish — for domain experts)
9. Tech stack

---

## Packaging & GitHub Pages

- `pyproject.toml` with `requires-python = ">=3.9"` and three dependencies
- `.gitignore`: standard Python + `.DS_Store` + `.env`
- `LICENSE`: MIT
- GitHub Pages: serve from `docs/` folder → `https://rubendelafuente.github.io/lc-graph/`

---

## Out of scope

- CI/CD, GitHub Actions, Makefile
- Unit tests
- Contribution guides

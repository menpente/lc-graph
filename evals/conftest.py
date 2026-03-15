# evals/conftest.py
"""Fixtures and configuration for eval tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

GOLDEN_DIR = Path(__file__).parent / "datasets" / "golden"


@pytest.fixture
def golden_resolucion_01() -> dict:
    """Returns {'texto': str, 'meta': dict} for resolucion_01 golden fixture."""
    texto = (GOLDEN_DIR / "resolucion_01.txt").read_text(encoding="utf-8")
    meta = json.loads((GOLDEN_DIR / "resolucion_01_meta.json").read_text(encoding="utf-8"))
    return {"texto": texto, "meta": meta}

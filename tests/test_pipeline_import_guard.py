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

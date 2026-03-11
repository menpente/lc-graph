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

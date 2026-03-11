import asyncio

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from evaluador_lc.models import InformeFinal
from evaluador_lc.pipeline import crear_grafo

app = FastAPI(title="Evaluador Lenguaje Claro")

_grafo = crear_grafo()


class EvaluateRequest(BaseModel):
    texto: str = Field(..., min_length=1)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/evaluate", response_model=InformeFinal)
async def evaluate(request: EvaluateRequest):
    try:
        resultado = await asyncio.to_thread(_grafo.invoke, {"texto": request.texto})
        return resultado["informe_final"]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

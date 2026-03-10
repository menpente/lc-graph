"""Modelos Pydantic para el pipeline de evaluación de lenguaje claro."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class Evaluacion(str, Enum):
    SI = "Sí"
    NO = "No"
    NO_COMPETE = "No compete"


class TipologiaDocumental(str, Enum):
    RESOLUCION = "resolución"
    NOTIFICACION = "notificación"
    CARTA = "carta"
    FORMULARIO = "formulario"
    ACTA = "acta"
    INFORME = "informe"
    CIRCULAR = "circular"
    DECRETO = "decreto"
    CONVOCATORIA = "convocatoria"
    INSTRUCCION = "instrucción"
    OTRO = "otro"


# ── Resultado de cada ítem ───────────────────────────────────────────────────

class ItemEvaluado(BaseModel):
    """Resultado de la evaluación de un único ítem."""
    seccion: int = Field(..., description="Número de sección (1-5)")
    item: str = Field(..., description="Descripción breve del ítem evaluado")
    evaluacion: Evaluacion
    comentario: str = Field(
        ...,
        max_length=300,
        description="Comentario breve, máx. 2 frases, con ejemplos del texto",
    )


# ── Output de cada sub-agente evaluador ──────────────────────────────────────

class ResultadoSeccion(BaseModel):
    """Resultado completo de un sub-agente evaluador de sección."""
    seccion: int
    nombre_seccion: str
    items: list[ItemEvaluado]


# ── Output del clasificador ──────────────────────────────────────────────────

class ResultadoClasificacion(BaseModel):
    """Output del SA-0: clasificador de documento."""
    tipologia: TipologiaDocumental
    justificacion: str = Field(
        ..., description="Breve justificación de la tipología asignada"
    )


# ── Puntuaciones ─────────────────────────────────────────────────────────────

class PuntuacionSeccion(BaseModel):
    seccion: int
    nombre: str
    total_evaluables: int
    total_si: int
    total_no: int
    total_no_compete: int
    porcentaje: Optional[float] = Field(
        None, description="Porcentaje de Sí sobre evaluables"
    )


class PuntuacionGlobal(BaseModel):
    puntuacion_general: float
    secciones: list[PuntuacionSeccion]


# ── Informe final ────────────────────────────────────────────────────────────

class InformeFinal(BaseModel):
    puntuacion: PuntuacionGlobal
    puntos_fuertes: list[str]
    areas_mejora: list[str]
    resumen_narrativo: str
    tabla_detallada: list[ItemEvaluado]

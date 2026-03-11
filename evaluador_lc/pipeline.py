"""
Pipeline LangGraph para evaluación de lenguaje claro.

Arquitectura:
  FASE 0: SA-0 Clasificador  →  determina tipología documental
  FASE 1: SA-1..SA-5          →  evaluación paralela de 5 secciones (41 ítems)
  FASE 2: SA-6a Calculador    →  puntuaciones (Python puro)
          SA-6b Sintetizador   →  resumen narrativo (LLM)

Uso:
  from evaluador_lc.pipeline import crear_grafo
  grafo = crear_grafo()
  resultado = grafo.invoke({"texto": "..."})
"""

from __future__ import annotations

import json
import operator
from typing import Annotated, Any, TypedDict

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from evaluador_lc.models import (
    Evaluacion,
    InformeFinal,
    ItemEvaluado,
    PuntuacionGlobal,
    PuntuacionSeccion,
    ResultadoClasificacion,
    ResultadoSeccion,
)
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


# ═══════════════════════════════════════════════════════════════════════════════
# Estado del grafo
# ═══════════════════════════════════════════════════════════════════════════════


def _merge_resultados(
    existing: list[ResultadoSeccion], new: list[ResultadoSeccion]
) -> list[ResultadoSeccion]:
    """Reducer para mergear resultados parciales de las ramas paralelas."""
    return existing + new


class EstadoPipeline(TypedDict):
    """Estado compartido entre todos los nodos del grafo."""

    # Input
    texto: str

    # Fase 0
    tipologia: str
    justificacion_tipologia: str

    # Fase 1 — los resultados se acumulan con el reducer
    resultados_secciones: Annotated[list[ResultadoSeccion], _merge_resultados]

    # Fase 2
    puntuacion: PuntuacionGlobal | None
    informe_final: InformeFinal | None


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _limpiar_json(texto: str) -> str:
    """Elimina fences de markdown si el LLM las incluye."""
    texto = texto.strip()
    if texto.startswith("```"):
        texto = texto.split("\n", 1)[1] if "\n" in texto else texto[3:]
    if texto.endswith("```"):
        texto = texto[:-3]
    return texto.strip()


def _llamar_llm(llm: ChatGroq, prompt: str) -> dict:
    """Llama al LLM y parsea la respuesta JSON."""
    response = llm.invoke([HumanMessage(content=prompt)])
    return json.loads(_limpiar_json(response.content))


# ═══════════════════════════════════════════════════════════════════════════════
# Nodos del grafo
# ═══════════════════════════════════════════════════════════════════════════════


def nodo_clasificador(state: EstadoPipeline) -> dict:
    """SA-0: Clasifica el tipo de documento."""
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, max_tokens=500)
    prompt = PROMPT_CLASIFICADOR.format(texto=state["texto"])
    resultado = _llamar_llm(llm, prompt)
    parsed = ResultadoClasificacion(**resultado)
    return {
        "tipologia": parsed.tipologia.value,
        "justificacion_tipologia": parsed.justificacion,
    }


def _crear_nodo_evaluador(seccion: int):
    """Factory: crea un nodo evaluador para una sección específica."""

    def nodo_evaluador(state: EstadoPipeline) -> dict:
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, max_tokens=4096)
        prompt = PROMPTS_SECCIONES[seccion].format(
            texto=state["texto"],
            tipologia=state["tipologia"],
        )
        resultado = _llamar_llm(llm, prompt)

        # Parsear ítems
        items = [ItemEvaluado(**item) for item in resultado["items"]]
        seccion_result = ResultadoSeccion(
            seccion=resultado["seccion"],
            nombre_seccion=resultado["nombre_seccion"],
            items=items,
        )
        return {"resultados_secciones": [seccion_result]}

    nodo_evaluador.__name__ = f"nodo_evaluador_s{seccion}"
    return nodo_evaluador


def nodo_calculador(state: EstadoPipeline) -> dict:
    """SA-6a: Calcula puntuaciones (Python puro, sin LLM)."""
    resultados = state["resultados_secciones"]

    nombres_secciones = {
        1: "Facilita la localización",
        2: "Mejora la comprensión (ideas)",
        3: "Mejora la comprensión (personaliza y humaniza)",
        4: "Mejora la comprensión (elige palabras sencillas)",
        5: "Facilita la toma de decisiones",
    }

    secciones_puntuacion: list[PuntuacionSeccion] = []
    total_evaluables_global = 0
    total_si_global = 0

    for sec_num in range(1, 6):
        # Buscar la sección en los resultados
        sec_result = next(
            (r for r in resultados if r.seccion == sec_num), None
        )
        if sec_result is None:
            continue

        total_si = sum(1 for i in sec_result.items if i.evaluacion == Evaluacion.SI)
        total_no = sum(1 for i in sec_result.items if i.evaluacion == Evaluacion.NO)
        total_nc = sum(
            1 for i in sec_result.items if i.evaluacion == Evaluacion.NO_COMPETE
        )
        evaluables = total_si + total_no

        porcentaje = round((total_si / evaluables) * 100, 1) if evaluables > 0 else None

        secciones_puntuacion.append(
            PuntuacionSeccion(
                seccion=sec_num,
                nombre=nombres_secciones[sec_num],
                total_evaluables=evaluables,
                total_si=total_si,
                total_no=total_no,
                total_no_compete=total_nc,
                porcentaje=porcentaje,
            )
        )

        total_evaluables_global += evaluables
        total_si_global += total_si

    puntuacion_general = (
        round((total_si_global / total_evaluables_global) * 100, 1)
        if total_evaluables_global > 0
        else 0.0
    )

    puntuacion = PuntuacionGlobal(
        puntuacion_general=puntuacion_general,
        secciones=secciones_puntuacion,
    )

    return {"puntuacion": puntuacion}


def nodo_sintetizador(state: EstadoPipeline) -> dict:
    """SA-6b: Genera resumen narrativo con LLM."""
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3, max_tokens=2048)

    puntuacion = state["puntuacion"]
    resultados = state["resultados_secciones"]

    # Preparar puntuaciones como texto
    lineas_punt = [
        f"Puntuación general: {puntuacion.puntuacion_general}%"
    ]
    for sec in puntuacion.secciones:
        lineas_punt.append(
            f"  Sección {sec.seccion} – {sec.nombre}: {sec.porcentaje}%"
        )

    # Recopilar ítems con "No"
    items_no = []
    for sec_result in resultados:
        for item in sec_result.items:
            if item.evaluacion == Evaluacion.NO:
                items_no.append(
                    f"  [S{item.seccion}] {item.item}: {item.comentario}"
                )

    prompt = PROMPT_SINTETIZADOR.format(
        tipologia=state["tipologia"],
        puntuaciones="\n".join(lineas_punt),
        items_no="\n".join(items_no) if items_no else "(ningún ítem con No)",
    )

    resultado = _llamar_llm(llm, prompt)

    # Construir tabla detallada completa
    tabla_detallada = []
    for sec_result in sorted(resultados, key=lambda r: r.seccion):
        tabla_detallada.extend(sec_result.items)

    informe = InformeFinal(
        puntuacion=puntuacion,
        puntos_fuertes=resultado.get("puntos_fuertes", []),
        areas_mejora=resultado.get("areas_mejora", []),
        resumen_narrativo=resultado.get("resumen_narrativo", ""),
        tabla_detallada=tabla_detallada,
    )

    return {"informe_final": informe}


# ═══════════════════════════════════════════════════════════════════════════════
# Construcción del grafo
# ═══════════════════════════════════════════════════════════════════════════════


def crear_grafo() -> StateGraph:
    """
    Construye y compila el grafo LangGraph.

    Flujo:
        clasificador
              │
              ▼
        ┌─────────────────────────────┐
        │  evaluadores S1..S5         │  (paralelo)
        └─────────────────────────────┘
              │
              ▼
         calculador  (Python puro)
              │
              ▼
         sintetizador (LLM)
              │
              ▼
             END
    """

    builder = StateGraph(EstadoPipeline)

    # ── Añadir nodos ─────────────────────────────────────────────────────────
    builder.add_node("clasificador", nodo_clasificador)

    for sec in range(1, 6):
        builder.add_node(f"evaluador_s{sec}", _crear_nodo_evaluador(sec))

    builder.add_node("calculador", nodo_calculador)
    builder.add_node("sintetizador", nodo_sintetizador)

    # ── Entry point ──────────────────────────────────────────────────────────
    builder.set_entry_point("clasificador")

    # ── Clasificador → fan-out a los 5 evaluadores ──────────────────────────
    for sec in range(1, 6):
        builder.add_edge("clasificador", f"evaluador_s{sec}")

    # ── Fan-in: los 5 evaluadores → calculador ──────────────────────────────
    for sec in range(1, 6):
        builder.add_edge(f"evaluador_s{sec}", "calculador")

    # ── Calculador → sintetizador → END ──────────────────────────────────────
    builder.add_edge("calculador", "sintetizador")
    builder.add_edge("sintetizador", END)

    return builder.compile()


# ═══════════════════════════════════════════════════════════════════════════════
# Formateador de salida
# ═══════════════════════════════════════════════════════════════════════════════


def formatear_informe(informe: InformeFinal) -> str:
    """Formatea el informe final como texto legible."""
    lineas = []

    # Puntuación general
    p = informe.puntuacion
    lineas.append("=" * 70)
    lineas.append(f"  PUNTUACIÓN GENERAL: {p.puntuacion_general}%")
    lineas.append("=" * 70)
    lineas.append("")

    # Desglose por sección
    lineas.append("DESGLOSE POR SECCIÓN:")
    for sec in p.secciones:
        pct = f"{sec.porcentaje}%" if sec.porcentaje is not None else "N/A"
        lineas.append(f"  Sección {sec.seccion} – {sec.nombre}: {pct}")
    lineas.append("")

    # Resumen
    lineas.append("─" * 70)
    lineas.append("PUNTOS FUERTES:")
    for punto in informe.puntos_fuertes:
        lineas.append(f"  ✓ {punto}")
    lineas.append("")

    lineas.append("ÁREAS DE MEJORA:")
    for area in informe.areas_mejora:
        lineas.append(f"  ✗ {area}")
    lineas.append("")

    lineas.append("RESUMEN:")
    lineas.append(f"  {informe.resumen_narrativo}")
    lineas.append("")

    # Tabla detallada
    lineas.append("─" * 70)
    lineas.append("TABLA DETALLADA")
    lineas.append("─" * 70)
    lineas.append(
        f"{'Sec':<5} {'Ítem':<45} {'Eval.':<12} {'Comentario'}"
    )
    lineas.append("─" * 70)
    for item in informe.tabla_detallada:
        item_text = (
            item.item[:43] + ".." if len(item.item) > 45 else item.item
        )
        lineas.append(
            f"{item.seccion:<5} {item_text:<45} {item.evaluacion.value:<12} {item.comentario}"
        )

    return "\n".join(lineas)

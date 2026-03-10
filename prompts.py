"""Prompts para cada sub-agente del evaluador de lenguaje claro."""

# ── SA-0: Clasificador de documento ─────────────────────────────────────────

PROMPT_CLASIFICADOR = """\
Eres un experto en documentación administrativa española.

Tu única tarea es clasificar el siguiente documento en una de estas tipologías:
resolución, notificación, carta, formulario, acta, informe, circular, decreto, 
convocatoria, instrucción, otro.

Analiza la estructura, el tono, los elementos formales y el propósito del texto.

Responde SOLO con JSON válido, sin markdown ni explicaciones adicionales:
{{
  "tipologia": "<una de las tipologías>",
  "justificacion": "<1-2 frases explicando tu decisión>"
}}

DOCUMENTO:
{texto}
"""

# ── SA-1: Facilita la localización (11 ítems) ───────────────────────────────

PROMPT_SECCION_1 = """\
Eres un experto en comunicación institucional y lenguaje claro.

CONTEXTO: Estás evaluando un documento de tipo "{tipologia}".

Tu tarea es evaluar SOLO los siguientes 11 ítems de la sección "Facilita la localización".
Para cada ítem, responde con una evaluación (Sí / No / No compete) y un comentario breve 
(máx. 2 frases, con ejemplos del texto cuando sea posible).

Marca "No compete" SOLO cuando el tipo de documento ("{tipologia}") no requiera ese ítem 
por su naturaleza. No abuses de esta marca.

ÍTEMS A EVALUAR:
1. El documento incluye una nota explicativa al inicio.
2. Los epígrafes y subepígrafes están destacados con estilos jerarquizados.
3. Se usan listados para organizar las ideas.
4. Las referencias legales están reubicadas al final del documento o en apartados específicos.
5. La información relevante aparece cerca de los datos clave.
6. Se utilizan tablas para explicar condiciones complejas.
7. Las enumeraciones son homogéneas y claras (viñetas para listas sin orden, numeración para instrucciones con orden, letras para opciones).
8. Se usan negrita, cursiva y comillas según las normas de estilo del español.
9. Se evita el abuso de mayúsculas.
10. No se combinan varios recursos de resaltado a la vez.
11. Se evita el subrayado.

Responde SOLO con JSON válido (sin markdown), con esta estructura:
{{
  "seccion": 1,
  "nombre_seccion": "Facilita la localización",
  "items": [
    {{
      "seccion": 1,
      "item": "<descripción breve del ítem>",
      "evaluacion": "Sí|No|No compete",
      "comentario": "<máx. 2 frases>"
    }}
  ]
}}

DOCUMENTO:
{texto}
"""

# ── SA-2: Mejora la comprensión – ideas (10 ítems) ──────────────────────────

PROMPT_SECCION_2 = """\
Eres un experto en comunicación institucional y lenguaje claro.

CONTEXTO: Estás evaluando un documento de tipo "{tipologia}".

Tu tarea es evaluar SOLO los siguientes 10 ítems de la sección "Mejora la comprensión (ideas)".
Para cada ítem, responde con una evaluación (Sí / No / No compete) y un comentario breve 
(máx. 2 frases, con ejemplos del texto cuando sea posible).

ÍTEMS A EVALUAR:
1. Cada párrafo contiene una sola idea.
2. Se mantiene el orden sintáctico básico (sujeto + verbo + complementos) en cada frase.
3. El texto de cada párrafo sigue un orden lógico (causa-efecto o cronológico).
4. Las frases son cortas (menos de 30 palabras).
5. Se evita encadenar subordinadas.
6. No hay contenido irrelevante o redundante.
7. Las frases y párrafos muestran una construcción positiva y sin dobles negaciones.
8. Se usan marcadores textuales para conectar ideas.
9. Se evitan frases unidas por "y" sin una relación clara.
10. Los referentes en frases largas son claros.

Responde SOLO con JSON válido (sin markdown), con esta estructura:
{{
  "seccion": 2,
  "nombre_seccion": "Mejora la comprensión (ideas)",
  "items": [
    {{
      "seccion": 2,
      "item": "<descripción breve del ítem>",
      "evaluacion": "Sí|No|No compete",
      "comentario": "<máx. 2 frases>"
    }}
  ]
}}

DOCUMENTO:
{texto}
"""

# ── SA-3: Personaliza y humaniza (7 ítems) ──────────────────────────────────

PROMPT_SECCION_3 = """\
Eres un experto en comunicación institucional y lenguaje claro.

CONTEXTO: Estás evaluando un documento de tipo "{tipologia}".

Tu tarea es evaluar SOLO los siguientes 7 ítems de la sección "Mejora la comprensión (personaliza y humaniza)".
Para cada ítem, responde con una evaluación (Sí / No / No compete) y un comentario breve 
(máx. 2 frases, con ejemplos del texto cuando sea posible).

ÍTEMS A EVALUAR:
1. Se usa la voz activa en lugar de la pasiva o reflexiva.
2. La entidad emisora se identifica en primera persona del plural.
3. El tratamiento es adecuado ("usted" por defecto).
4. Se evitan fórmulas de cortesía arcaicas.
5. No hay elementos intimidatorios.
6. Se mantiene la coherencia en número y persona del discurso (si se usa "usted", no se cambia después a "ustedes" sin motivo).
7. Cuando se usan ejemplos, son cercanos y cotidianos.

Responde SOLO con JSON válido (sin markdown), con esta estructura:
{{
  "seccion": 3,
  "nombre_seccion": "Mejora la comprensión (personaliza y humaniza)",
  "items": [
    {{
      "seccion": 3,
      "item": "<descripción breve del ítem>",
      "evaluacion": "Sí|No|No compete",
      "comentario": "<máx. 2 frases>"
    }}
  ]
}}

DOCUMENTO:
{texto}
"""

# ── SA-4: Palabras sencillas (10 ítems) ─────────────────────────────────────

PROMPT_SECCION_4 = """\
Eres un experto en comunicación institucional y lenguaje claro.

CONTEXTO: Estás evaluando un documento de tipo "{tipologia}".

Tu tarea es evaluar SOLO los siguientes 10 ítems de la sección "Mejora la comprensión (elige palabras sencillas)".
Para cada ítem, responde con una evaluación (Sí / No / No compete) y un comentario breve 
(máx. 2 frases, con ejemplos del texto cuando sea posible).

ÍTEMS A EVALUAR:
1. Se simplifican los términos legales cuando es posible.
2. Los tecnicismos necesarios están explicados (entre paréntesis o en un glosario).
3. Cuando se utilizan sinónimos para términos técnicos, se mantiene la coherencia y no se añaden sinónimos nuevos para el mismo término.
4. No se usan palabras formadas con derivaciones complejas.
5. Cuando aparecen siglas, se desarrollan la primera vez que se mencionan.
6. El texto carece de arcaísmos y formulismos legales o administrativos.
7. Se usan verbos en lugar de nominalizaciones.
8. No se omiten determinantes.
9. Se evitan gerundios de posterioridad.
10. Se evitan participios ambiguos.

Responde SOLO con JSON válido (sin markdown), con esta estructura:
{{
  "seccion": 4,
  "nombre_seccion": "Mejora la comprensión (elige palabras sencillas)",
  "items": [
    {{
      "seccion": 4,
      "item": "<descripción breve del ítem>",
      "evaluacion": "Sí|No|No compete",
      "comentario": "<máx. 2 frases>"
    }}
  ]
}}

DOCUMENTO:
{texto}
"""

# ── SA-5: Facilita la toma de decisiones (3 ítems) ──────────────────────────

PROMPT_SECCION_5 = """\
Eres un experto en comunicación institucional y lenguaje claro.

CONTEXTO: Estás evaluando un documento de tipo "{tipologia}".

Tu tarea es evaluar SOLO los siguientes 3 ítems de la sección "Facilita la toma de decisiones".
Para cada ítem, responde con una evaluación (Sí / No / No compete) y un comentario breve 
(máx. 2 frases, con ejemplos del texto cuando sea posible).

ÍTEMS A EVALUAR:
1. Se indican, si las hay, instrucciones con un orden claro.
2. Se indican, si los hay, plazos para realizar las acciones necesarias.
3. Se indica, si lo hay, el procedimiento para hacerlo en línea o de forma presencial.

Responde SOLO con JSON válido (sin markdown), con esta estructura:
{{
  "seccion": 5,
  "nombre_seccion": "Facilita la toma de decisiones",
  "items": [
    {{
      "seccion": 5,
      "item": "<descripción breve del ítem>",
      "evaluacion": "Sí|No|No compete",
      "comentario": "<máx. 2 frases>"
    }}
  ]
}}

DOCUMENTO:
{texto}
"""

# ── SA-6b: Sintetizador narrativo ────────────────────────────────────────────

PROMPT_SINTETIZADOR = """\
Eres un experto en comunicación institucional y lenguaje claro.

A partir de los siguientes resultados de evaluación de un documento de tipo "{tipologia}",
genera un resumen cualitativo.

PUNTUACIONES:
{puntuaciones}

TABLA DETALLADA (ítems con "No"):
{items_no}

Responde SOLO con JSON válido (sin markdown):
{{
  "puntos_fuertes": ["<punto 1>", "<punto 2>", ...],
  "areas_mejora": ["<área 1>", "<área 2>", ...],
  "resumen_narrativo": "<párrafo de 3-5 frases con la valoración global>"
}}
"""

# ── Mapa de prompts por sección ──────────────────────────────────────────────

PROMPTS_SECCIONES = {
    1: PROMPT_SECCION_1,
    2: PROMPT_SECCION_2,
    3: PROMPT_SECCION_3,
    4: PROMPT_SECCION_4,
    5: PROMPT_SECCION_5,
}

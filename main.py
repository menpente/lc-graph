"""
Punto de entrada para el evaluador de lenguaje claro.

Uso:
  # Evaluar un archivo de texto
  python -m evaluador_lc.main documento.txt

  # Evaluar texto por stdin
  cat documento.txt | python -m evaluador_lc.main

  # Desde código
  from evaluador_lc import crear_grafo, formatear_informe
  grafo = crear_grafo()
  resultado = grafo.invoke({"texto": "..."})
  print(formatear_informe(resultado["informe_final"]))
"""

from __future__ import annotations

import sys
from pathlib import Path

from evaluador_lc.pipeline import crear_grafo, formatear_informe


# ── Documento de ejemplo para pruebas ────────────────────────────────────────

DOCUMENTO_EJEMPLO = """\
RESOLUCIÓN DE CONCESIÓN DE AYUDA PARA ADQUISICIÓN DE VIVIENDA

Vista la solicitud presentada por D./Dña. __________, con DNI __________,
en fecha __________, y de conformidad con lo establecido en el Real Decreto
XXX/2024, de XX de XXXXX, por el que se regula el programa de ayudas directas
a la adquisición de vivienda habitual, y habida cuenta de que se cumplen los
requisitos exigidos en el artículo 5 del mencionado Real Decreto, esta
Dirección General ha tenido a bien RESOLVER:

PRIMERO. Conceder al/a la solicitante una ayuda directa por importe de
__________ euros (€) para la adquisición de su vivienda habitual.

SEGUNDO. El beneficiario deberá aportar, en el plazo de QUINCE (15) días
hábiles contados desde la notificación de la presente resolución, la
siguiente documentación:
a) Escritura de compraventa debidamente inscrita en el Registro de la Propiedad.
b) Certificado de empadronamiento en la vivienda adquirida.
c) Declaración responsable de no haber percibido otras ayudas incompatibles,
   quedando obligado a reintegrar las cantidades percibidas en caso de
   incumplimiento, siéndole de aplicación lo dispuesto en el artículo 37
   de la Ley 38/2003, de 17 de noviembre, General de Subvenciones.

TERCERO. Contra la presente resolución, que no pone fin a la vía
administrativa, podrá interponerse recurso de alzada ante el/la titular de
la Secretaría de Estado de Vivienda, en el plazo de UN (1) MES a contar
desde el día siguiente al de su notificación, de conformidad con lo
dispuesto en los artículos 121 y 122 de la Ley 39/2015, de 1 de octubre,
del Procedimiento Administrativo Común de las Administraciones Públicas.

En Madrid, a __ de __________ de 2024.
EL/LA DIRECTOR/A GENERAL DE VIVIENDA
"""


def main():
    # Leer texto: desde archivo, stdin, o usar ejemplo
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if not path.exists():
            print(f"Error: no se encontró el archivo '{path}'")
            sys.exit(1)
        texto = path.read_text(encoding="utf-8")
        print(f"📄 Evaluando: {path.name}")
    elif not sys.stdin.isatty():
        texto = sys.stdin.read()
        print("📄 Evaluando texto desde stdin")
    else:
        texto = DOCUMENTO_EJEMPLO
        print("📄 Evaluando documento de ejemplo (resolución administrativa)")

    print("⏳ Iniciando pipeline...\n")

    # Crear y ejecutar el grafo
    grafo = crear_grafo()
    resultado = grafo.invoke({"texto": texto})

    # Formatear y mostrar
    informe = resultado["informe_final"]
    print(formatear_informe(informe))


if __name__ == "__main__":
    main()

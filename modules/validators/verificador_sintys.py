"""
validators/verificador_sintys.py
--------------------------------
Valida el informe SINTyS.

Criterios de OK (`expediente.sintys_ok = True`):
    • Informe detectado.
    • Secciones “INVALIDEZ”  +  “Sin datos de Discapacidad”.
    • Secciones “FALLECIDO” +  “Sin datos de Fallecimiento”.
    • (Opcional) Si aparece “RELACIONES FAMILIARES”, debe seguir “Sin datos de Familiares”.
    • Se extrae y registra el CUIL encontrado en la cabecera.

Las incoherencias de CUIL se manejan luego por `Expediente.verificar_consistencia_cuiles()`.
"""

from __future__ import annotations

import re
from typing import Final

from modules.helpers.cuils import extraer_cuil
from modules.models.expediente import Expediente

# ──────────────────────────── patrones ────────────────────────────
P_SECCION: Final[re.Pattern[str]] = re.compile(
    r"(consulta\s+sintys|persona\s+identificada)", flags=re.I
)

P_CUIL: Final[re.Pattern[str]] = re.compile(
    r"cuil\s*:\s*([0-9\s-]{10,})", flags=re.I
)

# Palabras clave y sus “sin datos…”
P_INV: Final[str] = "INVALIDEZ"
P_INV_SD: Final[str] = "SIN DATOS DE DISCAPACIDAD"
P_FALL: Final[str] = "FALLECIDO"
P_FALL_SD: Final[str] = "SIN DATOS DE FALLECIMIENTO"
P_REL: Final[str] = "RELACIONES FAMILIARES"
P_REL_SD: Final[str] = "SIN DATOS DE FAMILIARES"


# ──────────────────────────── función ─────────────────────────────
def verificar_sintys(expediente: Expediente, texto_pdf: str) -> None:  # noqa: D401
    """
    Aplica las reglas de validación descritas arriba.
    """
    if not P_SECCION.search(texto_pdf):
        expediente.agregar_observacion("No se encontró Informe SINTyS (CONSULTA SINTyS).")
        return

    expediente.sintys_detectado = True
    texto_upper = texto_pdf.upper()

    # ── chequeos de secciones ─────────────────────────────────────
    invalidez_ok = P_INV in texto_upper and P_INV_SD in texto_upper
    fallecido_ok = P_FALL in texto_upper and P_FALL_SD in texto_upper

    if not P_INV in texto_upper:
        expediente.agregar_observacion("Informe SINTyS: Falta la sección 'INVALIDEZ'.")
    elif P_INV in texto_upper and P_INV_SD not in texto_upper:
        expediente.agregar_observacion(
            "Informe SINTyS: 'INVALIDEZ' sin la leyenda 'Sin datos de Discapacidad'."
        )

    if not P_FALL in texto_upper:
        expediente.agregar_observacion("Informe SINTyS: Falta la sección 'FALLECIDO'.")
    elif P_FALL in texto_upper and P_FALL_SD not in texto_upper:
        expediente.agregar_observacion(
            "Informe SINTyS: 'FALLECIDO' sin la leyenda 'Sin datos de Fallecimiento'."
        )

    # (Opcional) Relaciones familiares
    if P_REL in texto_upper and P_REL_SD not in texto_upper:
        expediente.agregar_observacion(
            "Informe SINTyS: 'RELACIONES FAMILIARES' sin la leyenda 'Sin datos de Familiares'."
        )

    # ── extracción y registro del CUIL ────────────────────────────
    if m_cuil := P_CUIL.search(texto_pdf):
        if cuil := extraer_cuil(m_cuil.group(1)):
            expediente.registrar_cuil("SINTYS", cuil)
    else:
        expediente.agregar_observacion("Informe SINTyS presente, pero no se pudo extraer CUIL.")

    # ── estado final ───────────────────────────────────────────────
    expediente.sintys_ok = invalidez_ok and fallecido_ok

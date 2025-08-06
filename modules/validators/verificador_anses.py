"""
validators/verificador_anses.py
-------------------------------
Valida el informe “INFORME - ANSES”.

• Detecta si el informe existe.
• Marca `anses_completo = False` cuando hay demasiados “NO CONSULTADO” o
  “SIN INFORMACIÓN”.
• Extrae CUIL y Nro. Documento del encabezado y llama
  `expediente.registrar_cuil("ANSES", cuil)`.
"""

from __future__ import annotations

import re
from typing import Final

from modules.helpers.cuils import extraer_cuil
from modules.models.expediente import Expediente

# ──────────────────────────── patrones ────────────────────────────
P_INFORME: Final[re.Pattern[str]] = re.compile(r"INFORME\s*-\s*ANSES", re.I)
P_BLOQUE: Final[re.Pattern[str]] = re.compile(
    r"INFORME\s*-\s*ANSES(.*?)(?:\n\s*\n|$)", re.I | re.S
)

# textos que indican ausencia de datos
P_NO_CONS: Final[re.Pattern[str]] = re.compile(r"\bNO\s+CONSULTADO\b", re.I)
P_SIN_INF: Final[re.Pattern[str]] = re.compile(r"\bSIN\s+INFORMACI[ÓO]N\b", re.I)

# encabezado (CUIL y DNI)
# patrón más flexible: ‘CUIL’ opcionalmente con dos puntos,
# seguido de cualquier whitespace y dígitos/guiones/espacios
P_CUIL: Final[re.Pattern[str]] = re.compile(
    r"CUIL\s*:?\s*([\d\s-]{10,})", re.I
)
P_DNI: Final[re.Pattern[str]] = re.compile(r"Nro\.\s*Documento\s*:\s*(\d+)", re.I)

LIMITE_INCOMPLETO = 7  # ≥7 ocurrencias ⇒ informe incompleto


# ──────────────────────────── función ─────────────────────────────
def verificar_anses(expediente: Expediente, texto_pdf: str) -> None:
    """
    • Marca `anses_detectado`.
    • Determina `anses_completo` en base a la cantidad de “SIN INFORMACIÓN” /
      “NO CONSULTADO”.
    • Registra el CUIL detectado en la cabecera.
    """
    if not P_INFORME.search(texto_pdf):
        # Informe no presente -> nada que hacer
        return

    expediente.anses_detectado = True

    # ── aislar el bloque “INFORME - ANSES” ─────────────────────────
    m_bloque = P_BLOQUE.search(texto_pdf)
    bloque = m_bloque.group(1) if m_bloque else texto_pdf

    # ── chequeo de completitud ─────────────────────────────────────
    total_no_cons = len(P_NO_CONS.findall(bloque))
    total_sin_inf = len(P_SIN_INF.findall(bloque))

    if (total_no_cons >= LIMITE_INCOMPLETO) or (total_sin_inf >= LIMITE_INCOMPLETO):
        expediente.agregar_observacion(
            f"Informe ANSES incompleto: "
            f"{total_no_cons}×'NO CONSULTADO' / {total_sin_inf}×'SIN INFORMACIÓN'."
        )
        # anses_completo queda False (default)
    else:
        expediente.anses_completo = True

    # ── extracción de CUIL ────────────────────────────────────
    # Tomamos sólo las primeras ~6 líneas del bloque para evitar
    # que coincida algún CUIL de un familiar, por ejemplo.
    encabezado = "\n".join(bloque.splitlines()[:6])

    if m_cuil := P_CUIL.search(encabezado):
        if cuil := extraer_cuil(m_cuil.group(1)):
            expediente.registrar_cuil("ANSES", cuil)
    else:
        expediente.agregar_observacion("Informe ANSES presente, pero no se pudo extraer CUIL.")

    # (Opcional) DNI si lo querés utilizar más adelante
    # if m_dni := P_DNI.search(bloque):
    #     expediente.dni_anses = m_dni.group(1)

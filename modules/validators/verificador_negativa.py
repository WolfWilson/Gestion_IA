"""
validators/verificador_negativa.py
----------------------------------
Valida la “Certificación Negativa” descargada desde servicioswww.anses.gob.ar.

Criterios de OK (`expediente.certneg_ok = True`)
    • La última página contiene la URL
      'servicioswww.anses.gob.ar/censite/Antecedentes.aspx'.
    • (Opcional) Se registra el CUIL hallado en dicha página.

Observaciones:
    • Si no se puede abrir la página o no aparece la URL.
    • Si no se extrae CUIL.
"""

from __future__ import annotations

import re
from typing import Final

import pdfplumber

from modules.helpers.cuils import extraer_cuil
from modules.models.expediente import Expediente

URL_OK: Final[str] = "servicioswww.anses.gob.ar/censite/Antecedentes.aspx"
P_CUIL: Final[re.Pattern[str]] = re.compile(r"\b(?:20|23|24|27|30)\d{9}\b")
P_DNI: Final[re.Pattern[str]] = re.compile(r"\b\d{7,8}\b")


# ──────────────────────────── función ─────────────────────────────
def verificar_certneg(expediente: Expediente) -> None:  # noqa: D401
    """
    Analiza la última página del PDF del expediente.
    """
    try:
        with pdfplumber.open(expediente.ruta_pdf) as pdf:
            last_text = (pdf.pages[-1].extract_text() or "")
    except Exception as exc:
        expediente.agregar_observacion(
            f"Error al leer última página para Cert. Neg.: {exc}"
        )
        return

    expediente.certneg_detectada = True
    text_lower = last_text.lower()

    # ── URL de verificación ────────────────────────────────────────
    if URL_OK.lower() in text_lower:
        expediente.certneg_ok = True
    else:
        expediente.agregar_observacion(
            "Certificación Negativa: no se detectó la URL de verificación "
            f"'{URL_OK}'."
        )

    # ── extracción de CUIL ─────────────────────────────────────────
    if m_cuil := P_CUIL.search(last_text.replace(" ", "")):
        expediente.registrar_cuil("NEGATIVA", m_cuil.group(0))
    else:
        expediente.agregar_observacion(
            "Certificación Negativa presente, pero no se pudo extraer CUIL."
        )

    # ── (Opcional) extracción de DNI ───────────────────────────────
    # if m_dni := P_DNI.search(last_text):
    #     expediente.dni_negativa = m_dni.group(0)

"""
validators/verificador_caratula.py
----------------------------------
Detecta la carátula (solicitud de jubilación ordinaria) dentro del texto PDF.
"""

from __future__ import annotations

import re
from typing import Final

from modules.models.expediente import Expediente

# Regex flexible (mayúsculas, acentos y espacios múltiples)
_PATRON_CARATULA: Final[re.Pattern[str]] = re.compile(
    r"solicita\s+jubilaci[oó]n\s+ordinaria",
    flags=re.IGNORECASE,
)


def verificar_caratula(expediente: Expediente, texto_pdf: str) -> None:
    """
    Marca ``expediente.caratula_encontrada`` cuando halla la leyenda típica
    de la carátula; de lo contrario, agrega observación.
    """
    if _PATRON_CARATULA.search(texto_pdf):
        expediente.caratula_encontrada = True
    else:
        expediente.agregar_observacion(
            "No se encontró Carátula (leyenda 'Solicita Jubilación Ordinaria')."
        )

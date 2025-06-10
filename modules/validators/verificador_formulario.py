"""
validators/verificador_formulario.py
------------------------------------
Detecta el “Formulario de Inicio” y, si es posible, extrae el CUIL para
comparación.
"""

from __future__ import annotations

import re
from typing import Final

from modules.helpers.cuils import extraer_cuil
from modules.models.expediente import Expediente

_PATRON_FORMULARIO: Final[re.Pattern[str]] = re.compile(
    r"formulario\s+de\s+inicio",
    flags=re.IGNORECASE,
)


def verificar_formulario_inicio(expediente: Expediente, texto_pdf: str) -> None:
    """
    1.  Activa ``expediente.formulario_inicio`` si encuentra la sección.
    2.  Intenta extraer el CUIL desde el propio formulario y llama
        ``expediente.registrar_cuil("FORMULARIO", cuil)``.
    """
    if _PATRON_FORMULARIO.search(texto_pdf):
        expediente.formulario_inicio = True

        # Opcional: capturar primer CUIL dentro del formulario
        if cuil := extraer_cuil(texto_pdf):
            expediente.registrar_cuil("FORMULARIO", cuil)
    else:
        expediente.agregar_observacion("No se encontró Formulario de Inicio.")

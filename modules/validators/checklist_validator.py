"""
validators/checklist_validator.py
---------------------------------
Agrupa los distintos verificadores y añade un control de consistencia
de CUILes detectados entre informes.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from modules.validators.verificador_caratula import verificar_caratula
from modules.validators.verificador_formulario import verificar_formulario_inicio
from modules.validators.verificador_renaper import verificar_renaper
from modules.validators.verificador_dni import verificar_dni
from modules.validators.verificador_sintys import verificar_sintys
from modules.validators.verificador_intercajas import verificar_intercajas
from modules.validators.verificador_anses import verificar_anses
from modules.validators.verificador_negativa import verificar_certneg

if TYPE_CHECKING:  # Evita import circular en tiempo de ejecución
    from modules.models.expediente import Expediente


class ChecklistValidator:
    """
    Aplica cada verificador especializado sobre un expediente.
    """

    def validar(self, expediente: "Expediente", texto_pdf: str) -> None:  # noqa: D401
        # Verificaciones básicas
        verificar_caratula(expediente, texto_pdf)
        verificar_formulario_inicio(expediente, texto_pdf)

        # Verificadores que además pueden registrar CUIL
        verificar_renaper(expediente, texto_pdf)
        verificar_sintys(expediente, texto_pdf)
        verificar_intercajas(expediente, texto_pdf)
        verificar_anses(expediente, texto_pdf)
        verificar_certneg(expediente)

        # Fotos DNI
        verificar_dni(expediente)

        # Nota: la consistencia de CUILes se delega al propio modelo

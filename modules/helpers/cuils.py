"""
helpers/cuil.py
---------------
Funciones utilitarias para manejo de CUIL / CUIT.

Se centraliza la lógica de extracción y validación para que,
si mañana cambia el formato o agregamos chequeo de dígito
verificador, lo toquemos en un solo lugar.
"""
from __future__ import annotations

import re
from typing import Final

_CUIL_REGEX: Final[re.Pattern[str]] = re.compile(r"(?:20|23|24|27|30)\d{9}")

def extraer_cuil(texto: str) -> str | None:
    """
    Devuelve el primer CUIL válido o None.

    • Elimina cualquier whitespace (espacios, tabulaciones, saltos de línea)
      y guiones antes de buscar.
    """
    # NORMALIZAR: quitar - y TODOS los espacios (\s cubre \n, \t, \r…)
    normalizado = re.sub(r"[\s-]+", "", texto)
    if m := _CUIL_REGEX.search(normalizado):
        return m.group(0)
    return None


def validar_cuil(cuil: str) -> bool:
    """
    Valida el CUIL usando el algoritmo tradicional de dígito verificador.
    Retorna **True** si es válido, **False** si el dígito verificador falla.
    """
    try:
        base, verif = cuil[:-1], int(cuil[-1])
        factores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        total = sum(int(d) * f for d, f in zip(base, factores))
        resto = 11 - (total % 11)
        calculado = 0 if resto in (11, 0) else resto
        return calculado == verif
    except Exception:
        return False

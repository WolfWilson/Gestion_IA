"""
validators/verificador_renaper.py
---------------------------------
Valida la “CONSULTA RENAPER” / “INFORME RENAPER”.

Criterios de OK (`expediente.renaper_completo = True`)
    • Se detecta la sección.
    • Existen al menos los campos obligatorios:
         - DNI
         - SEXO
         - FECHA CONSULTA
         - “DATOS REGISTRADOS EN EL RENAPER”
    • (Opcional) Se extrae y deja disponible el DNI.

Nota: el RENAPER **no** provee CUIL, por lo que no se registra en
`expediente.cuiles`.
"""

from __future__ import annotations

import re
from typing import Final

from modules.models.expediente import Expediente

# ──────────────────────────── patrones ────────────────────────────
P_SECCION: Final[re.Pattern[str]] = re.compile(
    r"(consulta\s+renaper|informe\s+renaper)", flags=re.I
)

P_DNI: Final[re.Pattern[str]] = re.compile(r"dni\s*:\s*(\d+)", flags=re.I)

CAMPOS_OBLIGATORIOS: Final[list[re.Pattern[str]]] = [
    re.compile(r"dni\s*:\s*\d+", re.I),
    re.compile(r"sexo\s*:\s*[fmox]", re.I),
    re.compile(r"fecha\s+consulta\s*:", re.I),
    re.compile(r"datos\s+registrados\s+en\s+el\s+renaper", re.I),
]


# ──────────────────────────── función ─────────────────────────────
def verificar_renaper(expediente: Expediente, texto_pdf: str) -> None:  # noqa: D401
    """
    • Marca `renaper_detectado`.
    • Evalúa `renaper_completo`.
    • Extrae el DNI (sin almacenarlo aún en `Expediente` salvo que decidas
      añadir un atributo).
    """
    if not P_SECCION.search(texto_pdf):
        expediente.agregar_observacion("No se encontró Informe/Consulta Renaper.")
        return

    expediente.renaper_detectado = True
    completo = True

    # ── campos obligatorios ───────────────────────────────────────
    for patron in CAMPOS_OBLIGATORIOS:
        if not patron.search(texto_pdf):
            completo = False
            break

    expediente.renaper_completo = completo
    if not completo:
        expediente.agregar_observacion("Informe Renaper INCOMPLETO: faltan campos clave.")

    # ── extracción de DNI (por si lo necesitás en el futuro) ──────
    if m_dni := P_DNI.search(texto_pdf):
        dni = m_dni.group(1)
        # Aquí podrías guardar en expediente.dni_renaper si decides
        # añadir ese atributo:
        # expediente.dni_renaper = dni
    else:
        expediente.agregar_observacion("Informe Renaper presente, pero no se pudo extraer DNI.")

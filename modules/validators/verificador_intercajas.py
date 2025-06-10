"""
validators/verificador_intercajas.py
------------------------------------
Valida la sección “CONSULTA INTERCAJAS” / “Certificación de Condición
Previsional” y registra el CUIL hallado.

Criterios de OK (`expediente.intercajas_ok = True`)
    • Se detecta la sección.
    • Existe la línea   "No se encontraron beneficios otorgados con el CUIL ingresado."
    • (Opcional) Se logra extraer el CUIL y se registra (las incoherencias las
      maneja `Expediente.registrar_cuil`).
"""

from __future__ import annotations

import re
from typing import Final

from modules.helpers.cuils import extraer_cuil
from modules.models.expediente import Expediente

# ──────────────────────────── patrones ────────────────────────────
# Frases que indican la sección Intercajas
P_SECCION: Final[re.Pattern[str]] = re.compile(
    r"(consulta\s+intercajas|certificaci[oó]n\s+de\s+condici[oó]n\s+previsional)",
    flags=re.I,
)

# Línea típica sin beneficios
P_LINEA_OK: Final[re.Pattern[str]] = re.compile(
    r"no\s+se\s+encontraron\s+beneficios\s+otorgados\s+con\s+el\s+cuil\s+ingresado",
    flags=re.I,
)

# Captura del CUIL inmediatamente después de la sección
# Ej: "Certificación de Condición Previsional - CUIL 27170117943"
P_CUIL: Final[re.Pattern[str]] = re.compile(
    r"cuil\s+([0-9\s-]{11,})",
    flags=re.I,
)


# ──────────────────────────── función ─────────────────────────────
def verificar_intercajas(expediente: Expediente, texto_pdf: str) -> None:  # noqa: D401
    """
    • Marca `intercajas_detectado` cuando encuentra la sección.
    • Verifica si incluye la línea sin-beneficios.
    • Extrae y registra el CUIL.
    """
    if not P_SECCION.search(texto_pdf):
        expediente.agregar_observacion(
            "No se encontró Informe Intercajas (CONSULTA INTERCAJAS / Cert. Condición Previsional)."
        )
        return  # nada más que hacer

    expediente.intercajas_detectado = True

    # ── línea de beneficios ────────────────────────────────────────
    linea_ok = bool(P_LINEA_OK.search(texto_pdf))
    if not linea_ok:
        expediente.agregar_observacion(
            "Informe Intercajas: falta la línea "
            "'No se encontraron beneficios otorgados con el CUIL ingresado.'"
        )

    # ── extracción de CUIL ─────────────────────────────────────────
    if m_cuil := P_CUIL.search(texto_pdf):
        if cuil := extraer_cuil(m_cuil.group(1)):
            expediente.registrar_cuil("INTERCAJAS", cuil)
    else:
        expediente.agregar_observacion(
            "Informe Intercajas presente, pero no se pudo extraer CUIL."
        )

    # ── estado final ───────────────────────────────────────────────
    expediente.intercajas_ok = linea_ok

"""
exportador.py
-------------
Genera un CSV con los resultados del análisis.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from modules.helpers.cuils import extraer_cuil
from modules.models.expediente import Expediente

EXPORTS_DIR: Path = Path("logs")
EXPORTS_DIR.mkdir(exist_ok=True)


def _cuil_coherente(expediente: Expediente) -> bool:
    """
    Consideramos coherente si todos los CUILes registrados son iguales.
    """
    valores = {c for c in expediente.cuiles.values() if c}
    return len(valores) <= 1


def exportar_a_csv(nombre_base: str, expedientes: List[Expediente]) -> Path:
    """
    Crea un CSV en `logs/nombre_base.csv`.

    Columnas:
        #, Ruta, CUIL(es), Coherencia, Error de lectura, Observaciones
    """
    ruta_csv = EXPORTS_DIR / f"{nombre_base}.csv"

    with ruta_csv.open(mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "#",
                "Ruta Archivo",
                "CUIL(es) detectados",
                "CUIL coherente",
                "Error de Lectura",
                "Observaciones (resumen)",
            ]
        )

        for i, exp in enumerate(expedientes, 1):
            cuiles = "; ".join(f"{k}:{v}" for k, v in exp.cuiles.items() if v) or "—"
            coherente = "✅" if _cuil_coherente(exp) else "⚠"
            obs = " | ".join(exp.observaciones) if exp.observaciones else "—"
            writer.writerow(
                [
                    i,
                    exp.ruta_pdf,
                    cuiles,
                    coherente,
                    "❌" if exp.error_lectura else "✅",
                    obs,
                ]
            )

    return ruta_csv

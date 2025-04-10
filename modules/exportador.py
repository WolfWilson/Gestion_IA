# modules/exportador.py
import csv
from pathlib import Path

EXPORTS_DIR = Path("logs")
EXPORTS_DIR.mkdir(exist_ok=True)

def exportar_a_csv(nombre_base, resultados):
    ruta_csv = EXPORTS_DIR / f"{nombre_base}.csv"

    with open(ruta_csv, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["#", "Ruta Archivo", "Resumen", "CUIL Detectado", "Error de Lectura"])

        for i, (ruta, resumen) in enumerate(resultados, 1):
            cuil = extraer_cuil(resumen)
            error = "Error" in resumen
            writer.writerow([i, ruta, resumen, cuil if cuil else "NO DETECTADO", "❌" if error else "✅"])

    return ruta_csv

def extraer_cuil(texto):
    import re
    match = re.search(r"\b(20|23|24|27|30)\d{9}\b", texto)
    return match.group(0) if match else None

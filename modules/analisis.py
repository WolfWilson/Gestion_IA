# modules/analisis.py
import re
import os
import datetime
import pdfplumber
import logging
from pathlib import Path

from modules.exportador import exportar_a_csv, extraer_cuil

logging.getLogger("pdfminer").setLevel(logging.ERROR)

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

PATRON_ARCHIVO = re.compile(r"^[A-Z]-\d{6}-\d{4}\.pdf$", re.IGNORECASE)

def extraer_texto_pdf(ruta_pdf, max_caracteres=500):
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            texto = ""
            for pagina in pdf.pages:
                texto += pagina.extract_text() or ""
                if len(texto) >= max_caracteres:
                    break
            return texto.strip().replace("\n", " ")[:max_caracteres]
    except Exception as e:
        return f"❌ Error al leer: {e}"

def analizar_expedientes(ruta_base: str):
    archivos_encontrados = []

    for root, _, files in os.walk(ruta_base):
        for archivo in files:
            if PATRON_ARCHIVO.match(archivo):
                ruta_completa = os.path.join(root, archivo)
                resumen = extraer_texto_pdf(ruta_completa)
                archivos_encontrados.append((ruta_completa, resumen))

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_base = f"expedientes_{timestamp}"

    # Exportar CSV
    ruta_csv = exportar_a_csv(nombre_base, archivos_encontrados)

    # Generar log TXT
    log_path = LOG_DIR / f"log_{nombre_base}.txt"
    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"📁 Análisis de Expedientes - {timestamp}\n")
        log.write(f"Ruta base: {ruta_base}\n")
        log.write(f"Total archivos válidos encontrados: {len(archivos_encontrados)}\n\n")

        cuil_detectados = 0
        errores_lectura = 0

        for i, (ruta, resumen) in enumerate(archivos_encontrados, 1):
            cuil = extraer_cuil(resumen)
            if "❌ Error" in resumen:
                errores_lectura += 1
            if cuil:
                cuil_detectados += 1

            log.write(f"{i}. 📄 {ruta}\n")
            log.write(f"   📝 Resumen: {resumen}\n\n")

        log.write("\n📊 Resumen Final:\n")
        log.write(f"▪ Expedientes procesados: {len(archivos_encontrados)}\n")
        log.write(f"▪ Expedientes con CUIL detectado: {cuil_detectados}\n")
        log.write(f"▪ Expedientes con error de lectura: {errores_lectura}\n")
        log.write(f"\n🗂 CSV generado: {ruta_csv}\n")

    print(f"✅ Análisis completado.\n- Log: {log_path}\n- CSV: {ruta_csv}")

"""
controllers/verificacion_expediente.py
--------------------------------------
Orquestador principal para el análisis masivo de expedientes PDF.
"""

from __future__ import annotations

import datetime
import logging
import os
import re
from pathlib import Path
from typing import Final, List

from modules.models.expediente import Expediente
from modules.services.lector_pdf import leer_texto_pdf
from modules.validators.checklist_validator import ChecklistValidator
from modules.exportador import exportar_a_csv
from modules.helpers.cuils import extraer_cuil

logging.getLogger("pdfminer").setLevel(logging.ERROR)

LOG_DIR: Final[Path] = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Patrón de archivo: E-000001-2025.pdf (letra, 6 dígitos, 4 dígitos)
PATRON_ARCHIVO: Final[re.Pattern[str]] = re.compile(
    r"^[A-Z]-\d{6}-\d{4}\.pdf$", re.IGNORECASE
)


class VerificacionExpedienteController:
    def __init__(self) -> None:
        self.validator = ChecklistValidator()

    # ───────────────────────── Procesamiento individual ──────────────────────────
    def procesar_expediente(self, ruta_pdf: str) -> Expediente:
        exp = Expediente(ruta_pdf)

        try:
            texto = leer_texto_pdf(ruta_pdf)
        except Exception as exc:
            exp.error_lectura = True
            exp.agregar_observacion(f"Error al leer PDF: {exc}")
            return exp

        # CUIL “global” (el primero que aparezca en el documento completo)
        if cuil := extraer_cuil(texto):
            exp.registrar_cuil("GLOBAL", cuil)

        # Otras validaciones (carátula, Renaper, SINTyS, etc.).
        self.validator.validar(exp, texto)

        # Consistencia final de CUIL ⇒ agrega observación si hay discrepancias
        exp.verificar_consistencia_cuiles()

        return exp

    # ───────────────────────── Procesamiento en lote ────────────────────────────
    def procesar_carpeta(self, ruta_base: str) -> List[Expediente]:
        expedientes: List[Expediente] = []

        for root, _, files in os.walk(ruta_base):
            for archivo in files:
                if PATRON_ARCHIVO.match(archivo):
                    ruta_pdf = os.path.join(root, archivo)
                    expedientes.append(self.procesar_expediente(ruta_pdf))

        # Informes finales
        self._generar_informes(expedientes, ruta_base)
        return expedientes

    # ───────────────────────── Generación de reportes ────────────────────────────
    def _generar_informes(self, expedientes: List[Expediente], ruta_base: str) -> None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_base = f"expedientes_{timestamp}"

        # 1) CSV
        ruta_csv = exportar_a_csv(nombre_base, expedientes)

        # 2) Log de texto detallado
        log_path = LOG_DIR / f"log_{nombre_base}.txt"
        with open(log_path, "w", encoding="utf-8") as fp:
            fp.write(f"📁 Análisis de Expedientes - {timestamp}\n")
            fp.write(f"Ruta base: {ruta_base}\n")
            fp.write(f"Total archivos válidos encontrados: {len(expedientes)}\n\n")

            # Contadores
            cont = {
                "error": 0,
                "caratula": 0,
                "formulario": 0,
                "renaper_det": 0,
                "renaper_comp": 0,
                "sintys_det": 0,
                "sintys_ok": 0,
                "intercajas_det": 0,
                "intercajas_ok": 0,
                "fotos": 0,
                "cuil": 0,
                "cuil_coherente": 0,
            }

            for e in expedientes:
                fp.write(f"Expediente: {e.ruta_pdf}\n")
                fp.write(f"  - Carátula: {e.caratula_encontrada}\n")
                fp.write(f"  - Formulario de Inicio: {e.formulario_inicio}\n")
                fp.write(f"  - Renaper detectado / completo: {e.renaper_detectado} / {e.renaper_completo}\n")
                fp.write(f"  - SINTyS detectado / OK: {e.sintys_detectado} / {e.sintys_ok}\n")
                fp.write(f"  - Intercajas detectado / OK: {e.intercajas_detectado} / {e.intercajas_ok}\n")
                fp.write(f"  - Fotos DNI (frente + dorso): {e.fotos_dni_front and e.fotos_dni_back}\n")
                fp.write(f"  - CUILes detectados: {e.cuiles}\n")
                fp.write(f"  - CUIL coherente: {e.cuil_coherente}\n")
                fp.write(f"  - ANSES detectado / completo: {e.anses_detectado} / {e.anses_completo}\n")
                fp.write(f"  - Cert. Negativa detectada / OK: {e.certneg_detectada} / {e.certneg_ok}\n")

                if e.observaciones:
                    fp.write("  - Observaciones:\n")
                    for obs in e.observaciones:
                        fp.write(f"      • {obs}\n")
                fp.write("\n")

                # Actualizar contadores
                if e.error_lectura:
                    cont["error"] += 1
                if e.caratula_encontrada:
                    cont["caratula"] += 1
                if e.formulario_inicio:
                    cont["formulario"] += 1
                if e.renaper_detectado:
                    cont["renaper_det"] += 1
                if e.renaper_completo:
                    cont["renaper_comp"] += 1
                if e.sintys_detectado:
                    cont["sintys_det"] += 1
                if e.sintys_ok:
                    cont["sintys_ok"] += 1
                if e.intercajas_detectado:
                    cont["intercajas_det"] += 1
                if e.intercajas_ok:
                    cont["intercajas_ok"] += 1
                if e.fotos_dni_front and e.fotos_dni_back:
                    cont["fotos"] += 1
                if e.cuiles:
                    cont["cuil"] += 1
                if e.cuil_coherente:
                    cont["cuil_coherente"] += 1

            # Resumen
            fp.write("📊 Resumen Final\n")
            for k, v in cont.items():
                fp.write(f"  ▪ {k.replace('_', ' ').title()}: {v}\n")
            fp.write(f"\n🗂 CSV generado: {ruta_csv}\n")

        print(f"✅ Análisis completado.\n- Log: {log_path}\n- CSV: {ruta_csv}")

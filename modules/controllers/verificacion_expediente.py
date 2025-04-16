# modules/controllers/verificacion_expediente.py

import os
import re
import datetime
import logging
from pathlib import Path

from modules.models.expediente import Expediente
from modules.services.lector_pdf import leer_texto_pdf
from modules.validators.checklist_validator import ChecklistValidator

from modules.exportador import exportar_a_csv, extraer_cuil

logging.getLogger("pdfminer").setLevel(logging.ERROR)

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Patrón de archivo: E-000001-2025.pdf (letra, 6 dígitos, 4 dígitos)
PATRON_ARCHIVO = re.compile(r"^[A-Z]-\d{6}-\d{4}\.pdf$", re.IGNORECASE)


class VerificacionExpedienteController:

    def __init__(self):
        self.validator = ChecklistValidator()

    def procesar_expediente(self, ruta_pdf: str) -> Expediente:
        """
        Crea un objeto Expediente, extrae el texto del PDF, detecta el CUIL,
        y ejecuta las validaciones definidas en ChecklistValidator.
        """
        exp = Expediente(ruta_pdf)
        try:
            texto = leer_texto_pdf(ruta_pdf)
        except Exception as e:
            exp.error_lectura = True
            exp.agregar_observacion(f"Error al leer PDF: {e}")
            return exp

        # Detectar CUIL
        cuil = extraer_cuil(texto)
        exp.cuil = cuil

        # Aplicar validaciones (carátula, renaper, sintys, intercajas, fotos DNI...)
        self.validator.validar(exp, texto)

        return exp

    def procesar_carpeta(self, ruta_base: str):
        """
        Recorre la carpeta y subcarpetas, filtra PDFs por PATRON_ARCHIVO,
        valida cada uno y luego genera un log + CSV con los resultados.
        Retorna la lista de Expedientes generados.
        """
        expedientes = []
        for root, _, files in os.walk(ruta_base):
            for archivo in files:
                if PATRON_ARCHIVO.match(archivo):
                    ruta_pdf = os.path.join(root, archivo)
                    exp = self.procesar_expediente(ruta_pdf)
                    expedientes.append(exp)

        # Generar informes (CSV + log)
        self._generar_informes(expedientes, ruta_base)
        return expedientes

    def _generar_informes(self, expedientes, ruta_base):
        """
        Crea un CSV y un log .txt con datos de los expedientes procesados,
        incluyendo contadores para cada tipo de informe o validación.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_base = f"expedientes_{timestamp}"

        # 1) Preparar datos para exportar a CSV: (ruta, resumen)
        datos_csv = []
        for e in expedientes:
            if e.error_lectura:
                resumen = f"❌ Error. Observaciones: {e.observaciones}"
            else:
                flags = (
                    f"Carátula={e.caratula_encontrada}, "
                    f"Formulario={e.formulario_inicio}, "
                    f"RenaperDet={e.renaper_detectado}, "
                    f"RenaperComp={e.renaper_completo}, "
                    f"SintysDet={e.sintys_detectado}, "
                    f"SintysOK={e.sintys_ok}, "
                    f"IntercajasDet={e.intercajas_detectado}, "
                    f"IntercajasOK={e.intercajas_ok}, "
                    f"FotosDNI={(e.fotos_dni_front and e.fotos_dni_back)}, "
                    f"CUIL={e.cuil}"
                )
                resumen = f"{flags}. Obs: {e.observaciones}"
            datos_csv.append((e.ruta_pdf, resumen))

        # Exportar CSV usando tu exportar_a_csv
        ruta_csv = exportar_a_csv(nombre_base, datos_csv)

        # 2) Generar log de texto
        log_path = LOG_DIR / f"log_{nombre_base}.txt"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"📁 Análisis de Expedientes - {timestamp}\n")
            f.write(f"Ruta base: {ruta_base}\n")
            f.write(f"Total archivos válidos encontrados: {len(expedientes)}\n\n")

            # Contadores
            caratula_ok = 0
            form_ok = 0
            renaper_ok = 0
            renaper_comp = 0
            sintys_detected_count = 0
            sintys_ok_count = 0
            intercajas_detected_count = 0
            intercajas_ok_count = 0
            fotos_ok = 0
            cuil_count = 0
            error_count = 0

            for e in expedientes:
                f.write(f"Expediente: {e.ruta_pdf}\n")
                f.write(f"  - Carátula: {e.caratula_encontrada}\n")
                f.write(f"  - Formulario de Inicio: {e.formulario_inicio}\n")
                f.write(f"  - Renaper detectado: {e.renaper_detectado}\n")
                f.write(f"  - Renaper completo: {e.renaper_completo}\n")
                f.write(f"  - Informe SINTyS detectado: {e.sintys_detectado}\n")
                f.write(f"  - Informe SINTyS OK: {e.sintys_ok}\n")
                f.write(f"  - Informe Intercajas detectado: {e.intercajas_detectado}\n")
                f.write(f"  - Informe Intercajas OK: {e.intercajas_ok}\n")
                f.write(f"  - Fotos DNI: {e.fotos_dni_front and e.fotos_dni_back}\n")
                f.write(f"  - CUIL: {e.cuil}\n")

                if e.observaciones:
                    f.write("  - Observaciones:\n")
                    for obs in e.observaciones:
                        f.write(f"    * {obs}\n")
                else:
                    f.write("  - Observaciones: Ninguna\n")
                f.write("\n")

                # Actualizar contadores
                if e.error_lectura:
                    error_count += 1
                if e.caratula_encontrada:
                    caratula_ok += 1
                if e.formulario_inicio:
                    form_ok += 1
                if e.renaper_detectado:
                    renaper_ok += 1
                if e.renaper_completo:
                    renaper_comp += 1
                if e.sintys_detectado:
                    sintys_detected_count += 1
                if e.sintys_ok:
                    sintys_ok_count += 1
                if e.intercajas_detectado:
                    intercajas_detected_count += 1
                if e.intercajas_ok:
                    intercajas_ok_count += 1
                if e.fotos_dni_front and e.fotos_dni_back:
                    fotos_ok += 1
                if e.cuil:
                    cuil_count += 1

            # Resumen final
            f.write("\n📊 Resumen Final:\n")
            f.write(f"▪ Expedientes procesados: {len(expedientes)}\n")
            f.write(f"▪ Error de lectura: {error_count}\n")
            f.write(f"▪ Carátula hallada: {caratula_ok}\n")
            f.write(f"▪ Formulario Inicio hallado: {form_ok}\n")
            f.write(f"▪ Informe Renaper detectado: {renaper_ok}\n")
            f.write(f"▪ Informe Renaper completo: {renaper_comp}\n")
            f.write(f"▪ Informe SINTyS detectado: {sintys_detected_count}\n")
            f.write(f"▪ Informe SINTyS OK: {sintys_ok_count}\n")
            f.write(f"▪ Informe Intercajas detectado: {intercajas_detected_count}\n")
            f.write(f"▪ Informe Intercajas OK: {intercajas_ok_count}\n")
            f.write(f"▪ Fotos DNI correctas: {fotos_ok}\n")
            f.write(f"▪ Expedientes con CUIL detectado: {cuil_count}\n")

            f.write(f"\n🗂 CSV generado: {ruta_csv}\n")

        print(f"✅ Análisis completado.\n- Log: {log_path}\n- CSV: {ruta_csv}")

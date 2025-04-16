# modules/validators/verificador_renaper.py
import re

def verificar_renaper(expediente, texto_pdf):
    """
    - Marca en expediente si 'renaper_detectado' = True/False
    - Marca 'renaper_completo' según contenga ciertos campos.
    - Agrega observaciones si falta algo.
    """
    # Buscamos “Consulta Renaper” o “Informe Renaper”
    patron_base = re.compile(r"(consulta renaper|informe renaper)", re.IGNORECASE)
    detectado = bool(patron_base.search(texto_pdf))
    expediente.renaper_detectado = detectado

    if not detectado:
        expediente.agregar_observacion("No se encontró Informe/Consulta Renaper.")
        return

    # Revisamos campos obligatorios: DNI:, SEXO:, FECHA CONSULTA:, DATOS REGISTRADOS...
    campos_obligatorios = [
        r"DNI:\s*\d+",
        r"SEXO:\s*[FMX]",
        r"FECHA\s+CONSULTA:",
        r"DATOS\s+REGISTRADOS\s+EN\s+EL\s+RENAPER"
    ]
    completo = True
    for patron in campos_obligatorios:
        if not re.search(patron, texto_pdf, flags=re.IGNORECASE):
            completo = False
            break

    expediente.renaper_completo = completo
    if not completo:
        expediente.agregar_observacion("Informe Renaper INCOMPLETO. Faltan campos.")

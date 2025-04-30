import pdfplumber

URL_OK = "servicioswww.anses.gob.ar/censite/Antecedentes.aspx"

def verificar_certneg(expediente):
    """
    • Abre la ÚLTIMA página del PDF.
    • Si aparece 'servicioswww.anses.gob.ar/censite/Antecedentes.aspx'
      → certneg_ok = True.
    • Si no aparece   → observación.
    """
    try:
        with pdfplumber.open(expediente.ruta_pdf) as pdf:
            ultima_pagina = pdf.pages[-1]
            texto = (ultima_pagina.extract_text() or "").lower()
    except Exception as e:
        expediente.agregar_observacion(f"Error al leer última página para Cert. Neg.: {e}")
        return

    expediente.certneg_detectada = True     # al menos se analizó la página

    if URL_OK.lower() in texto:
        expediente.certneg_ok = True
    else:
        expediente.agregar_observacion(
            "No se detectó el campo de verificación "
            "'servicioswww.anses.gob.ar/censite/Antecedentes.aspx' "
            "en la Certificación Negativa (última página)."
        )

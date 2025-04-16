# modules/validators/verificador_dni.py
from modules.services.lector_pdf import extraer_imagenes_pagina

def verificar_dni(expediente):
    """
    Verifica si en la página 2 y 3 hay al menos 2 imágenes en total.
    Asume que con 2 imágenes son frente y dorso.
    """
    total_imagenes = 0
    for page_idx in [1, 2]:  # 0-based: la 2da y 3ra pág
        imagenes = extraer_imagenes_pagina(expediente.ruta_pdf, page_idx)
        total_imagenes += len(imagenes)

    if total_imagenes >= 2:
        expediente.fotos_dni_front = True
        expediente.fotos_dni_back = True
    else:
        expediente.agregar_observacion("No se detectaron ambas fotos de DNI (pág.2 y 3).")

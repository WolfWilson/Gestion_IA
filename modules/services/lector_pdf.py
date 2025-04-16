# modules/services/lector_pdf.py

import pdfplumber

def leer_texto_pdf(ruta_pdf):
    """
    Retorna TODO el texto de un PDF como string.
    Si falla, lanza excepción (que luego capturás en tu controller).
    """
    texto = ""
    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            texto_pagina = pagina.extract_text() or ""
            texto += texto_pagina + "\n"
    return texto.strip()

def extraer_imagenes_pagina(ruta_pdf, page_index):
    """
    Devuelve la lista de metadatos de imágenes halladas en la página page_index.
    """
    with pdfplumber.open(ruta_pdf) as pdf:
        if page_index < len(pdf.pages):
            page = pdf.pages[page_index]
            return page.images  # Lista con info de cada imagen
    return []

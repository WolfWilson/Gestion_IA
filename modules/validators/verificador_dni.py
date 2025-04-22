import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from PIL import Image
import pytesseract # <--- Añadido para OSD (Orientación)
import pdfplumber
import re

# Asegúrate de que Tesseract esté instalado y, si es necesario, configura la ruta:
# Ejemplo: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# (Descomenta y ajusta la línea anterior si Tesseract no está en tu PATH)

from modules.services.lector_pdf import extraer_imagenes_pagina # Asumiendo que existe

OUT_DIR = Path("extracted_dni")
OUT_DIR_CROPPED = OUT_DIR / "cropped"
OUT_DIR.mkdir(exist_ok=True)
OUT_DIR_CROPPED.mkdir(exist_ok=True)

# ---------- Corrección de Orientación (NUEVO) --------------------------------
def _correct_orientation(img_bgr):
    """
    Detecta la orientación de la imagen usando Tesseract OSD y la rota.
    Devuelve la imagen rotada correctamente (0 grados).
    """
    try:
        # Usar image_to_osd para obtener información de orientación
        osd_data = pytesseract.image_to_osd(img_bgr, output_type=pytesseract.Output.DICT) # 'spa' para español ayuda
        rotation = osd_data.get('rotate', 0)
        # print(f"Detected rotation: {rotation} degrees") # Para depuración

        if rotation == 90:
            corrected_img = cv2.rotate(img_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif rotation == 180:
            corrected_img = cv2.rotate(img_bgr, cv2.ROTATE_180)
        elif rotation == 270:
            corrected_img = cv2.rotate(img_bgr, cv2.ROTATE_90_CLOCKWISE)
        else:
            corrected_img = img_bgr # Ya está orientada o no se pudo detectar bien
        return corrected_img
    except Exception as e:
        print(f"Error during OSD detection: {e}")
        # Si falla Tesseract OSD, devolver la imagen original
        return img_bgr

# ---------- OpenCV-based crop (Lógica de _crop_pil actualizada) -------------
def _crop_pil(img_bgr):
    """
    Recorta la imagen para eliminar bordes blancos/vacíos usando contornos de OpenCV.
    Devuelve la imagen recortada (ROI) o la imagen original si falla el recorte.
    """
    if img_bgr is None or img_bgr.size == 0:
        return img_bgr

    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # Aplicar desenfoque para reducir ruido y mejorar la detección de bordes/contornos
    img_blurred = cv2.GaussianBlur(img_gray, (5, 5), 0)

    # Umbralización: Usar Otsu para encontrar un umbral óptimo automáticamente.
    # THRESH_BINARY_INV para que el objeto (DNI) sea blanco y el fondo negro.
    _, img_thresh = cv2.threshold(img_blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Encontrar contornos
    contours, _ = cv2.findContours(img_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        # No se encontraron contornos, devolver original
        return img_bgr

    # Encontrar el contorno más grande (asumiendo que es el DNI)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Verificar si el contorno más grande tiene un área mínima razonable
    min_area_threshold = 0.01 * img_bgr.shape[0] * img_bgr.shape[1] # Ej: 1% del área total
    if cv2.contourArea(largest_contour) < min_area_threshold:
        # El contorno es demasiado pequeño, probablemente ruido, devolver original
         return img_bgr

    # Obtener el bounding box del contorno más grande
    x, y, w, h = cv2.boundingRect(largest_contour)

    # Añadir un pequeño margen (similar al original)
    expand = 10
    x1 = max(0, x - expand)
    y1 = max(0, y - expand)
    x2 = min(img_bgr.shape[1], x + w + expand)
    y2 = min(img_bgr.shape[0], y + h + expand)

    # Recortar la imagen original (a color) usando las coordenadas
    cropped_img = img_bgr[y1:y2, x1:x2]
    
    # Comprobar si el recorte es válido (a veces puede dar tamaño 0 si algo falla)
    if cropped_img.size == 0:
        return img_bgr # Devolver original si el recorte falló

    return cropped_img


# ---------- color (HSV) - Sin cambios --------------------------------------
def _es_color(img_bgr, sat_thr=40, pct_thr=0.04):
    """
    Verifica si una imagen es predominantemente a color basándose en la saturación HSV.
    img_bgr: Imagen en formato BGR de OpenCV.
    sat_thr: Umbral de saturación. Píxeles con saturación mayor se consideran 'color'.
    pct_thr: Umbral de porcentaje. Si el porcentaje de píxeles 'color' supera esto,
             la imagen se considera a color.
    Devuelve True si es a color, False si es B/N o escala de grises.
    """
    if img_bgr is None or img_bgr.size == 0:
        return False
    try:
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        # Calcular el porcentaje de píxeles cuya saturación supera el umbral
        # hsv[:, :, 1] es el canal de saturación
        color_pixel_ratio = np.mean(hsv[:, :, 1] > sat_thr)
        return color_pixel_ratio > pct_thr
    except cv2.error as e:
        # Puede ocurrir si la imagen tiene un formato inesperado
        print(f"Error converting to HSV or processing image for color check: {e}")
        return False # Asumir que no es color si hay error

# ---------- guardado auxiliar - Sin cambios ---------------------------------
def _save(img, folder, stem, page_idx, tag):
    """Guarda la imagen en la carpeta especificada con un nombre descriptivo."""
    if img is None or img.size == 0:
        print(f"Skipping save for {tag} on page {page_idx}, image is empty.")
        return
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        fname = f"{stem}_p{page_idx}_{tag}_{ts}.png"
        cv2.imwrite(str(folder / fname), img)
    except Exception as e:
        print(f"Error saving image {folder / fname}: {e}")


# ---------- verificador - Modificado para incluir corrección de orientación ---
def verificar_dni(expediente):
    """
    • Busca página Renaper, mira N páginas antes.
    • Extrae imágenes, corrige orientación, guarda raw orientado.
    • Recorta imágenes usando OpenCV, guarda ROI recortado.
    • Control: ≥2 imágenes y al menos una a color.
    """
    # 1) índice Renaper
    renaper_idx = None
    max_pages_to_check = 10 # Límite por si no encuentra Renaper
    pages_to_check_before_renaper = 3 # Número de páginas antes de Renaper a revisar
    
    try:
        with pdfplumber.open(expediente.ruta_pdf) as pdf:
            num_pages_pdf = len(pdf.pages)
            limit = min(num_pages_pdf, max_pages_to_check) # Limitar búsqueda inicial
            for i in range(limit): 
                page = pdf.pages[i]
                text = page.extract_text() or ""
                if re.search("CONSULTA RENAPER", text, re.I):
                    renaper_idx = i
                    break
            
            # Definir el rango de páginas a procesar
            if renaper_idx is not None:
                start_page = max(0, renaper_idx - pages_to_check_before_renaper)
                end_page = renaper_idx # Revisar hasta la página ANTERIOR a Renaper
            else:
                # Si no se encuentra Renaper, revisar las primeras N páginas como fallback
                start_page = 0
                end_page = min(num_pages_pdf, pages_to_check_before_renaper) # O ajusta según necesidad
                print(f"Advertencia: Página RENAPER no encontrada en {expediente.ruta_pdf}. Revisando primeras {end_page} páginas.")

            pages = range(start_page, end_page)

    except Exception as e:
        print(f"Error opening or processing PDF {expediente.ruta_pdf}: {e}")
        expediente.agregar_observacion(f"Error al procesar el PDF: {e}")
        return

    # --- Procesamiento de imágenes ---
    extracted_images_data = [] # Almacenará (p_idx, roi_image)
    stem = Path(expediente.ruta_pdf).stem
    color_results = []

    for p in pages:
        try:
            image_metas = extraer_imagenes_pagina(expediente.ruta_pdf, p)
        except Exception as e:
            print(f"Error extrayendo imágenes de página {p} para {stem}: {e}")
            continue
            
        for meta in image_metas:
            try:
                stream_data = meta["stream"].get_data()
                arr = np.frombuffer(stream_data, np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

                if img is None or img.size == 0:
                    # print(f"Skipping invalid image data on page {p} for {stem}.")
                    continue
                
                # --- 1. Corregir Orientación ---
                img_oriented = _correct_orientation(img)
                if img_oriented is None or img_oriented.size == 0:
                     print(f"Skipping image on page {p} after orientation check resulted in empty image.")
                     continue
                     
                _save(img_oriented, OUT_DIR, stem, p, "raw_oriented")

                # --- 2. Recortar ---
                roi = _crop_pil(img_oriented) # Usa la versión mejorada con OpenCV
                if roi is None or roi.size == 0:
                     print(f"Skipping image on page {p} after cropping resulted in empty image.")
                     continue
                     
                _save(roi, OUT_DIR_CROPPED, stem, p, "roi_cv")
                
                # Añadir info para chequeos posteriores
                extracted_images_data.append((p, roi))
                
                # --- 3. Chequear Color (del ROI) ---
                color_results.append(_es_color(roi)) # Chequea el color de la imagen recortada

            except MemoryError:
                 print(f"MemoryError processing an image on page {p} for {stem}. Skipping this image.")
                 continue # Saltar a la siguiente imagen si hay problemas de memoria
            except Exception as e:
                print(f"Error processing an image on page {p} for {stem}: {e}")
                continue # Continuar con la siguiente imagen si hay un error

    # --- Verificaciones finales ---
    if len(extracted_images_data) < 2:
        expediente.agregar_observacion(
            f"No se detectaron suficientes imágenes de DNI ({len(extracted_images_data)} encontradas) en las páginas {list(pages)}."
        )
        # Aunque no se encuentren 2, se podrían marcar como encontradas si alguna se halló
        if len(extracted_images_data) > 0:
             expediente.fotos_dni_front = True # O alguna lógica más fina si puedes distinguir frente/dorso
             # expediente.fotos_dni_back = ?
    else:
        # Se encontraron 2 o más, asumimos frente y dorso
        expediente.fotos_dni_front = True
        expediente.fotos_dni_back = True

    if not any(color_results):
         # Solo agregar observación si se encontraron imágenes pero NINGUNA es a color
         if len(extracted_images_data) > 0:
            expediente.agregar_observacion(
                "Las imágenes del DNI detectadas parecen estar en B/N o escala de grises (posible fotocopia)."
            )
        # Si no se encontraron imágenes, el mensaje anterior sobre cantidad ya es suficiente

    # futuros TODO: blur + OCR

# Ejemplo de cómo podrías llamar a la función (necesitas definir un objeto 'expediente')
# class MockExpediente:
#     def __init__(self, ruta):
#         self.ruta_pdf = ruta
#         self.observaciones = []
#         self.fotos_dni_front = False
#         self.fotos_dni_back = False
#
#     def agregar_observacion(self, obs):
#         print(f"OBSERVACION: {obs}")
#         self.observaciones.append(obs)
#
# # Crear un PDF de prueba o usar uno existente
# pdf_path = "ruta/a/tu/documento.pdf"
# if Path(pdf_path).exists():
#      exp = MockExpediente(pdf_path)
#      verificar_dni(exp)
#      print(f"Procesado: {exp.ruta_pdf}")
#      print(f"Foto Frente DNI detectada: {exp.fotos_dni_front}")
#      print(f"Foto Dorso DNI detectada: {exp.fotos_dni_back}")
#      print("Observaciones:", exp.observaciones)
# else:
#      print(f"Archivo PDF de prueba no encontrado en: {pdf_path}")
# modules/validators/verificador_dni.py
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime

from modules.services.lector_pdf import extraer_imagenes_pagina


OUT_DIR          = Path("extracted_dni")
OUT_DIR_CROPPED  = OUT_DIR / "cropped"
OUT_DIR.mkdir(exist_ok=True)
OUT_DIR_CROPPED.mkdir(exist_ok=True)


# ---------------- contorno DNI ----------------------------------------------
def _buscar_contorno_dni(img_bgr):
    """Devuelve cuatro puntos float32 del DNI o None si no lo halla."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gray, 50, 150)

    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL,
                               cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None

    h_img, w_img = gray.shape
    tarjetas = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area < 0.01 * w_img * h_img:        # descarta muy chico
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) != 4:
            continue
        # aspecto cercano a 1.6 (85.6mm/54mm)
        (x, y, w, h) = cv2.boundingRect(approx)
        ratio = w / h if h else 0
        if 1.4 < ratio < 1.8:
            tarjetas.append((area, approx.reshape(4, 2)))

    if not tarjetas:
        return None
    # el de mayor área compatible
    tarjetas.sort(key=lambda t: t[0], reverse=True)
    return tarjetas[0][1].astype("float32")


def _warp(img_bgr, pts_src, tamaño=(856, 540)):
    tl, tr, br, bl = pts_src
    pts_dst = np.array([[0, 0],
                        [tamaño[0]-1, 0],
                        [tamaño[0]-1, tamaño[1]-1],
                        [0, tamaño[1]-1]], dtype="float32")
    M = cv2.getPerspectiveTransform(pts_src, pts_dst)
    return cv2.warpPerspective(img_bgr, M, tamaño)


# ---------------- color ------------------------------------------------------
def _es_color(img_bgr, sat_thr=40, pct_thr=0.05):
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    return (hsv[:, :, 1] > sat_thr).mean() > pct_thr


# ---------------- guardado ---------------------------------------------------
def _save(img, dir_path, stem, page_idx, suffix):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    fname = f"{stem}_p{page_idx}_{suffix}_{ts}.png"
    cv2.imwrite(str(dir_path / fname), img)


# ---------------- verificador principal --------------------------------------
def verificar_dni(expediente):
    """
    1) Identifica págs previas a Renaper (3).
    2) Extrae imágenes, guarda original + ROI.
    3) Controla ≥2 imágenes y color.
    """
    # localizar renaper
    import pdfplumber
    renaper_idx = None
    with pdfplumber.open(expediente.ruta_pdf) as pdf:
        for idx, p in enumerate(pdf.pages):
            txt = (p.extract_text() or "").upper()
            if "CONSULTA RENAPER" in txt:
                renaper_idx = idx
                break
    pages = range(max(0, (renaper_idx or 4) - 3),
                  (renaper_idx or 4))

    imgs = []
    stem = Path(expediente.ruta_pdf).stem
    for p in pages:
        for meta in extraer_imagenes_pagina(expediente.ruta_pdf, p):
            try:
                raw = meta["stream"].get_data()
            except Exception:
                continue
            arr = np.frombuffer(raw, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                continue
            imgs.append((p, img))
            _save(img, OUT_DIR, stem, p, "raw")

    if len(imgs) < 2:
        expediente.agregar_observacion(
            "No se detectaron ambas fotos de DNI (páginas previas a Renaper)."
        )
        return
    expediente.fotos_dni_front = expediente.fotos_dni_back = True

    colores = []
    for p_idx, img in imgs:
        pts = _buscar_contorno_dni(img)
        roi = _warp(img, pts) if pts is not None else img
        _save(roi, OUT_DIR_CROPPED, stem, p_idx, "roi")
        colores.append(_es_color(roi))

    if not any(colores):
        expediente.agregar_observacion(
            "Las imágenes del DNI parecen en B/N (posible fotocopia)."
        )

    # TODO blur / OCR próximamente

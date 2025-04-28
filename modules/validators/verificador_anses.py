import re

# encabezado del bloque
P_INFORME = re.compile(r"INFORME\s*-\s*ANSES", re.I)

# bloque desde el encabezado hasta el salto doble o fin
P_BLOQUE  = re.compile(r"INFORME\s*-\s*ANSES(.*?)(?:\n\s*\n|$)", re.I | re.S)

# dos posibles textos que indican ausencia de datos
P_NO_CONS = re.compile(r"\bNO\s+CONSULTADO\b", re.I)
P_SIN_INF = re.compile(r"\bSIN\s+INFORMACI[ÓO]N\b", re.I)

LIMITE_INCOMPLETO = 7   # 7 o más ocurrencias ⇒ informe incompleto


def verificar_anses(expediente, texto_pdf):
    """Marca anses_completo = False si hay ≥7 'NO CONSULTADO' o 'SIN INFORMACIÓN'."""
    if not P_INFORME.search(texto_pdf):
        return                     # informe no presente

    expediente.anses_detectado = True

    # tomar solo el bloque ANSES
    bloque = P_BLOQUE.search(texto_pdf)
    bloque = bloque.group(1) if bloque else texto_pdf

    total_no_cons = len(P_NO_CONS.findall(bloque))
    total_sin_inf = len(P_SIN_INF.findall(bloque))

    if (total_no_cons >= LIMITE_INCOMPLETO) or (total_sin_inf >= LIMITE_INCOMPLETO):
        expediente.agregar_observacion(
            f"Informe ANSES incompleto: "
            f"{total_no_cons}×'NO CONSULTADO' / {total_sin_inf}×'SIN INFORMACIÓN'."
        )
        # anses_completo queda False (valor por defecto)
    else:
        expediente.anses_completo = True

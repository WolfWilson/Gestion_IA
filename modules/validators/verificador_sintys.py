# modules/validators/verificador_sintys.py

import re

def verificar_sintys(expediente, texto_pdf):
    """
    Chequea la presencia y 'completitud' de SINTyS según la lógica:
      1. Debe haber un bloque con "CONSULTA SINTyS" y/o "PERSONA IDENTIFICADA".
      2. Debe aparecer la palabra "INVALIDEZ", luego "Sin datos de Discapacidad".
      3. Debe aparecer la palabra "FALLECIDO", luego "Sin datos de Fallecimiento".
      4. (Opcional) 'RELACIONES FAMILIARES' y 'Sin datos de Familiares'.

    Si todo se cumple, expediente.sintys_ok = True.
    Caso contrario, se agregan observaciones.
    """

    # Detectar SINTyS
    patron_sintys = re.compile(r"(consulta\s+sintys|persona\s+identificada)", re.IGNORECASE)
    detectado = bool(patron_sintys.search(texto_pdf))
    expediente.sintys_detectado = detectado

    if not detectado:
        expediente.agregar_observacion("No se encontró Informe SINTyS (CONSULTA SINTyS).")
        return

    # Buscamos "INVALIDEZ" y "FALLECIDO"
    # Y que, después (en algún lado), aparezca "Sin datos de Discapacidad" y "Sin datos de Fallecimiento".
    invalidez_encontrado = "INVALIDEZ" in texto_pdf.upper()
    fallecido_encontrado = "FALLECIDO" in texto_pdf.upper()

    # Chequeo "Sin datos de Discapacidad"
    sin_discapacidad = "Sin datos de Discapacidad" in texto_pdf
    # Chequeo "Sin datos de Fallecimiento"
    sin_fallecimiento = "Sin datos de Fallecimiento" in texto_pdf

    # Lógica: Para decir que está "OK", necesitamos 
    # - "INVALIDEZ" + "Sin datos de Discapacidad"
    # - "FALLECIDO" + "Sin datos de Fallecimiento"
    # Si falta alguno, agregamos observación:
    if not invalidez_encontrado:
        expediente.agregar_observacion("Informe SINTyS: Falta la sección 'INVALIDEZ'.")
    else:
        if not sin_discapacidad:
            expediente.agregar_observacion("Informe SINTyS: No figura 'Sin datos de Discapacidad' tras INVALIDEZ.")

    if not fallecido_encontrado:
        expediente.agregar_observacion("Informe SINTyS: Falta la sección 'FALLECIDO'.")
    else:
        if not sin_fallecimiento:
            expediente.agregar_observacion("Informe SINTyS: No figura 'Sin datos de Fallecimiento' tras FALLECIDO.")

    # (Opcional) Chequear 'RELACIONES FAMILIARES' => 'Sin datos de Familiares'
    familiares_detectado = "RELACIONES FAMILIARES" in texto_pdf.upper()
    sin_familiares = "Sin datos de Familiares" in texto_pdf
    if familiares_detectado and not sin_familiares:
        expediente.agregar_observacion("Informe SINTyS: Hay 'RELACIONES FAMILIARES' pero no 'Sin datos de Familiares'.")

    # Decidir si todo está OK
    # => Se detectó SINTyS, y se cumplieron "Sin datos de Discapacidad/Fallecimiento" 
    #    para esas secciones
    if (invalidez_encontrado and sin_discapacidad 
        and fallecido_encontrado and sin_fallecimiento):
        expediente.sintys_ok = True
    else:
        # No marcamos True
        pass

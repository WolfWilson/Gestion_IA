# modules/validators/verificador_intercajas.py
import re

def verificar_intercajas(expediente, texto_pdf):
    """
    - Confirma que exista la sección "CONSULTA INTERCAJAS" (o algo similar).
    - Verifica la línea "No se encontraron beneficios otorgados con el CUIL ingresado."
    - Compara el CUIL encontrado en esa línea con expediente.cuil (si se parsea).
      O simplemente comprueba que la línea contenga el mismo cuil si está en expediente.
    - Si no cumple, se agregan observaciones.
    """
    # 1) Detectar Intercajas
    patron_base = re.compile(r"(consulta\s+intercajas|certificaci[oó]n\s+de\s+condici[oó]n\s+previsional)", re.IGNORECASE)
    detectado = bool(patron_base.search(texto_pdf))
    expediente.intercajas_detectado = detectado
    
    if not detectado:
        expediente.agregar_observacion("No se encontró Informe Intercajas (CONSULTA INTERCAJAS).")
        return

    # 2) Chequear la línea clave "No se encontraron beneficios otorgados con el CUIL ingresado."
    linea_ok = "No se encontraron beneficios otorgados con el CUIL ingresado." in texto_pdf
    if not linea_ok:
        expediente.agregar_observacion(
            "Informe Intercajas: No se detectó la línea 'No se encontraron beneficios...' => podría haber otro beneficio."
        )

    # 3) Comprobar coincidencia de CUIL si existe en ese fragmento
    #    El PDF tiene algo como: "CUIL 27121256733" y luego "No se encontraron beneficios..."
    #    Podemos verificar que contenga el mismo cuil que expedition.cuil
    if expediente.cuil:
        # Si el expediente tiene cuil=27121256733
        # Buscamos la parte "CUIL 27121256733" en el texto
        cuil_texto = f"CUIL {expediente.cuil}"
        if cuil_texto not in texto_pdf:
            expediente.agregar_observacion(
                "Informe Intercajas: El CUIL del expediente no coincide con el texto del informe."
            )
    else:
        # Si no hay cuil en expediente, no podemos verificar coincidencia
        expediente.agregar_observacion(
            "No se puede validar Intercajas contra CUIL, el expediente no tiene CUIL."
        )
    
    # 4) Decidir si todo está OK
    # => Se detectó Intercajas, la línea "No se encontraron beneficios..." existe,
    #    y el cuil coincide (si se tenía cuil).
    if detectado and linea_ok and expediente.cuil:
        cuil_texto = f"CUIL {expediente.cuil}"
        if cuil_texto in texto_pdf:
            expediente.intercajas_ok = True
        # Si no coincide, ya se agregó la observación
    # Si no => se mantiene false

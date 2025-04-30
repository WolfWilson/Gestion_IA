# modules/validators/checklist_validator.py
import re
from modules.validators.verificador_renaper import verificar_renaper
from modules.validators.verificador_dni import verificar_dni
from modules.validators.verificador_sintys import verificar_sintys
from modules.validators.verificador_intercajas import verificar_intercajas
from modules.validators.verificador_anses import verificar_anses
from modules.validators.verificador_negativa import verificar_certneg
def verificar_caratula(expediente, texto_pdf):
    if "SOLICITA Jubilación Ordinaria" in texto_pdf:
        expediente.caratula_encontrada = True
    else:
        expediente.agregar_observacion("No se encontró Carátula (SOLICITA Jubilación Ordinaria).")

def verificar_formulario_inicio(expediente, texto_pdf):
    if "FORMULARIO DE INICIO" in texto_pdf:
        expediente.formulario_inicio = True
    else:
        expediente.agregar_observacion("No se encontró Formulario de Inicio.")

class ChecklistValidator:
    def __init__(self):
        pass

    def validar(self, expediente, texto_pdf):
        # Carátula, Formulario
        verificar_caratula(expediente, texto_pdf)
        verificar_formulario_inicio(expediente, texto_pdf)

        # Renaper
        verificar_renaper(expediente, texto_pdf)

        # SINTyS
        verificar_sintys(expediente, texto_pdf)

        # Intercajas
        verificar_intercajas(expediente, texto_pdf)

        # DNI (fotos)
        verificar_dni(expediente)
        
        from modules.validators.verificador_anses import verificar_anses


        # ANSES 
        verificar_anses(expediente, texto_pdf)     # ← nuevo


        #  NEGATIVA 
        verificar_certneg(expediente)
        

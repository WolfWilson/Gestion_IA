# modules/models/expediente.py

class Expediente:
    def __init__(self, ruta_pdf: str):
        self.ruta_pdf = ruta_pdf
        self.caratula_encontrada = False
        self.formulario_inicio = False
        
        self.renaper_detectado = False
        self.renaper_completo = False
        
        # ---------- SINTyS ----------
        self.sintys_detectado = False
        self.sintys_ok = False  # "OK" significa que encontró las secciones y los "Sin datos" correspondientes.
        
        # DNI (fotos)
        self.fotos_dni_front = False
        self.fotos_dni_back = False
        
        self.cuil = None
        self.error_lectura = False
        self.observaciones = []

        #intercajas
        self.intercajas_detectado = False
        self.intercajas_ok = False  # "OK" significa que encontró las secciones y los "Sin datos" correspondientes.
    
    def agregar_observacion(self, mensaje: str):
        self.observaciones.append(mensaje)

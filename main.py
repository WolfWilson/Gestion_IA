# main.py
from modules.controllers.verificacion_expediente import VerificacionExpedienteController

def main():
    ruta = r"C:\Users\abouvier\Downloads\Digitalizacion_jubilaciones"
    controller = VerificacionExpedienteController()
    resultados = controller.procesar_carpeta(ruta)

    # Resumen en consola
    for exp in resultados:
        print(f"Expediente: {exp.ruta_pdf}")
        print("  - Carátula:", exp.caratula_encontrada)
        print("  - Formulario de Inicio:", exp.formulario_inicio)
        print("  - Renaper detectado:", exp.renaper_detectado)
        print("  - Renaper completo:", exp.renaper_completo)
        print("  - SINTyS detectado:", exp.sintys_detectado)
        print("  - SINTyS OK:", exp.sintys_ok)
        print("  - Fotos DNI:", exp.fotos_dni_front and exp.fotos_dni_back)
        print("  - CUIL:", exp.cuil)
        print("  - Informe de intercajas detectado:", exp.intercajas_detectado)
        print("  - Informe de intercajas OK:", exp.intercajas_ok)
        print("  - Observaciones:", exp.observaciones)
        print("  - Anses detectado:", exp.anses_detectado)
        print("  - Anses completo:", exp.anses_completo)
              

if __name__ == "__main__":
    main()
